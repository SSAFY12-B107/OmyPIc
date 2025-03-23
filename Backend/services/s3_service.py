# services/s3_service.py

import boto3
from botocore.exceptions import NoCredentialsError
from fastapi import HTTPException
import uuid
from core.config import settings

# S3 클라이언트 초기화
s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

async def upload_audio_to_s3(audio_data, problem_id):
    """
    오디오 파일을 S3에 업로드하고 URL을 반환합니다.
    
    Args:
        audio_data (bytes): 업로드할 오디오 파일 데이터
        problem_id (str): 문제 ID
        
    Returns:
        str: S3에 업로드된 파일의 URL
    """
    try:
        # 파일명 생성 (문제 ID + 고유 식별자)
        file_name = f"problem_audio/{problem_id}/{uuid.uuid4()}.mp3"
        
        # S3에 업로드
        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=file_name,
            Body=audio_data,
            ContentType='audio/mpeg'
        )
        
        # S3 URL 생성
        s3_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{file_name}"
        
        return s3_url
    
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS 자격 증명을 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 업로드 중 오류가 발생했습니다: {str(e)}")



# 다른 유형의 파일 업로드를 위한 일반 함수
async def upload_file_to_s3(file_data, folder, file_name, content_type):
    """
    일반 파일을 S3에 업로드하고 URL을 반환합니다.
    
    Args:
        file_data (bytes): 업로드할 파일 데이터
        folder (str): S3 폴더 경로
        file_name (str): 파일 이름
        content_type (str): 파일 콘텐츠 타입
        
    Returns:
        str: S3에 업로드된 파일의 URL
    """
    try:
        # 파일 경로 생성
        s3_path = f"{folder}/{file_name}"
        
        # S3에 업로드
        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=s3_path,
            Body=file_data,
            ContentType=content_type
        )
        
        # S3 URL 생성
        s3_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_path}"
        
        return s3_url
    
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS 자격 증명을 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 업로드 중 오류가 발생했습니다: {str(e)}")