# scripts/generate_and_upload_audio.py
import asyncio
import boto3
from botocore.exceptions import ClientError
import logging
import os
import tempfile
import uuid
from gtts import gTTS
from motor.motor_asyncio import AsyncIOMotorClient
import argparse
from bson import ObjectId

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioGenerator:
    def __init__(self, mongodb_url, db_name, aws_access_key_id=None, aws_secret_access_key=None, aws_region=None, bucket_name=None):
        self.mongodb_url = mongodb_url
        self.db_name = db_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        self.bucket_name = bucket_name
        
        # S3 클라이언트 초기화 (액세스 키가 제공된 경우)
        if aws_access_key_id and aws_secret_access_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=aws_region
            )
        else:
            # 환경 변수나 AWS CLI 구성에서 자격 증명 사용
            self.s3_client = boto3.client('s3', region_name=aws_region)
        
    async def connect_to_mongodb(self):
        """MongoDB에 연결"""
        try:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.db = self.client[self.db_name]
            logger.info(f"MongoDB에 연결됨: {self.mongodb_url}, DB: {self.db_name}")
            return True
        except Exception as e:
            logger.error(f"MongoDB 연결 오류: {str(e)}")
            return False

    async def close_mongodb(self):
        """MongoDB 연결 종료"""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("MongoDB 연결 종료됨")
    
    def generate_audio(self, text, file_path):
        """텍스트를 mp3로 변환"""
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(file_path)
            logger.info(f"오디오 생성 완료: {file_path}")
            return True
        except Exception as e:
            logger.error(f"오디오 생성 오류: {str(e)}")
            return False
    
    def upload_to_s3(self, file_path, object_key):
        """S3에 파일 업로드"""
        try:
            with open(file_path, 'rb') as file:
                self.s3_client.upload_fileobj(
                    file,
                    self.bucket_name,
                    object_key,
                    ExtraArgs={
                        'ContentType': 'audio/mpeg'
                    }
                )
            
            # S3 URL 생성
            url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{object_key}"
            logger.info(f"S3 업로드 완료: {url}")
            return url
        except ClientError as e:
            logger.error(f"S3 업로드 오류: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"예상치 못한 오류: {str(e)}")
            return None
    
    async def update_problem_audio_url(self, problem_id, audio_url):
        """problem 문서의 audio_s3_url 업데이트"""
        try:
            result = await self.db.problems.update_one(
                {"_id": ObjectId(problem_id) if isinstance(problem_id, str) else problem_id},
                {"$set": {"audio_s3_url": audio_url}}
            )
            
            if result.modified_count > 0:
                logger.info(f"문서 업데이트 성공: {problem_id}")
                return True
            else:
                logger.warning(f"문서를 찾을 수 없거나 변경되지 않음: {problem_id}")
                return False
        except Exception as e:
            logger.error(f"문서 업데이트 오류: {str(e)}")
            return False
    
    async def process_all_problems(self):
        """모든 problems 처리"""
        try:
            # MongoDB에서 모든 problems 조회
            problems = await self.db.problems.find().to_list(length=None)
            logger.info(f"총 {len(problems)} 개의 문제를 찾았습니다.")
            
            # 각 problem 처리
            success_count = 0
            fail_count = 0
            
            for problem in problems:
                problem_id = problem.get("_id")
                content = problem.get("content")
                
                if not content:
                    logger.warning(f"문제 {problem_id}에 content가 없습니다. 건너뜁니다.")
                    fail_count += 1
                    continue
                
                # 임시 파일 생성
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                try:
                    # 오디오 생성
                    if not self.generate_audio(content, temp_path):
                        logger.error(f"문제 {problem_id}의 오디오 생성 실패")
                        fail_count += 1
                        continue
                    
                    # S3 업로드용 고유 키 생성
                    object_key = f"omypic-MP3files/{str(problem_id)}.mp3"
                    
                    # S3 업로드
                    audio_url = self.upload_to_s3(temp_path, object_key)
                    if not audio_url:
                        logger.error(f"문제 {problem_id}의 S3 업로드 실패")
                        fail_count += 1
                        continue
                    
                    # MongoDB 업데이트
                    if await self.update_problem_audio_url(problem_id, audio_url):
                        success_count += 1
                    else:
                        fail_count += 1
                        
                finally:
                    # 임시 파일 삭제
                    try:
                        os.unlink(temp_path)
                    except Exception as e:
                        logger.error(f"임시 파일 삭제 오류: {str(e)}")
            
            logger.info(f"처리 완료: 성공 {success_count}, 실패 {fail_count}")
            return success_count, fail_count
        
        except Exception as e:
            logger.error(f"처리 중 오류 발생: {str(e)}")
            return 0, 0

async def main():
    parser = argparse.ArgumentParser(description='문제 content를 TTS로 변환하여 S3에 업로드하고 MongoDB에 URL 저장')
    parser.add_argument('--mongodb-url', required=True, help='MongoDB 연결 URL')
    parser.add_argument('--db-name', required=True, help='MongoDB 데이터베이스 이름')
    parser.add_argument('--bucket', required=True, help='S3 버킷 이름')
    parser.add_argument('--region', default='ap-northeast-2', help='AWS 리전 (기본값: ap-northeast-2)')
    parser.add_argument('--access-key', help='AWS 액세스 키 ID (환경 변수나 AWS CLI 구성에서 가져올 수도 있음)')
    parser.add_argument('--secret-key', help='AWS 시크릿 액세스 키 (환경 변수나 AWS CLI 구성에서 가져올 수도 있음)')
    
    args = parser.parse_args()
    
    # 환경 변수나 명령줄에서 자격 증명 가져오기
    access_key = args.access_key or os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = args.secret_key or os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    try:
        # 오디오 생성기 초기화
        generator = AudioGenerator(
            mongodb_url=args.mongodb_url,
            db_name=args.db_name,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_region=args.region,
            bucket_name=args.bucket
        )
        
        # MongoDB 연결
        if not await generator.connect_to_mongodb():
            print("MongoDB 연결에 실패했습니다. 스크립트를 종료합니다.")
            return
        
        # 모든 문제 처리
        success_count, fail_count = await generator.process_all_problems()
        
        print(f"처리 완료: 성공 {success_count}, 실패 {fail_count}")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
    finally:
        # MongoDB 연결 종료
        if 'generator' in locals():
            await generator.close_mongodb()

if __name__ == "__main__":
    # asyncio 이벤트 루프 실행
    asyncio.run(main())