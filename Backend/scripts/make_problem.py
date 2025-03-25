import pandas as pd
import uuid
import asyncio
import logging
import sys
import os

from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_mongodb():
    """MongoDB 연결"""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    return client[settings.MONGODB_DB_NAME]


# Excel 파일 읽기 및 데이터 가공
async def process_excel_and_save(file_path):
    # MongoDB 연결
    db = await get_mongodb()
    
    # Excel 파일 읽기
    df = pd.read_excel(file_path)
    
    # 필요한 컬럼이 있는지 확인
    required_columns = ["topic_category", "problem_category", "content", "connected_problem", "high_grade_kit"]
    for col in required_columns:
        if col not in df.columns:
            print(f"오류: '{col}' 컬럼이 없습니다.")
            return
    
    # 데이터 가공 및 MongoDB에 저장
    current_group_id = None
    order_in_group = 0
    
    for idx, row in df.iterrows():
        # 필요한 필드 추출
        has_connected = row.get("connected_problem") == "O"
        
        # 연결된 문제 그룹 관리
        if has_connected and order_in_group == 0:
            # 연결된 문제의 시작이면 새 그룹 ID 생성
            current_group_id = str(uuid.uuid4())
            order_in_group = 1
        elif order_in_group > 0:
            # 이전 문제가 연결된 문제라면 같은 그룹에 속함
            order_in_group += 1
            # 이 문제가 연결된 문제를 가지지 않으면 그룹의 마지막
            if not has_connected:
                current_group_id = None
                order_in_group = 0
        
        # topic_group 필드 설정
        # topic_group 컬럼이 있으면 해당 값 사용, 없으면 None
        topic_group = row.get("topic_group") if "topic_group" in df.columns else None
        
        # None이거나 NaN인 경우 None으로 설정
        if pd.isna(topic_group):
            topic_group = None
        
        # 문제 데이터 생성
        problem_data = {
            "topic_category": row["topic_category"],
            "problem_category": row["problem_category"],
            "content": row["content"],
            "audio_s3_url": str(row.get("audio_s3_url", "")) if not pd.isna(row.get("audio_s3_url", "")) else None,
            "high_grade_kit": bool(row.get("high_grade_kit", False)),
            "problem_group_id": current_group_id,
            "problem_order": order_in_group if order_in_group > 0 else 0,
            "topic_group": topic_group  # 새로 추가된 필드
        }
        
        # MongoDB에 저장
        result = await db.problems.insert_one(problem_data)
        print(f"문제 ID {result.inserted_id} 저장 완료: 그룹 {current_group_id}, 순서 {order_in_group}, 토픽 그룹 {topic_group}")

# 비동기 실행
async def main():
    file_path = "C:/Users/SSAFY/Desktop/pjt2/data/problem_data.xlsx"  # Excel 파일 경로
    await process_excel_and_save(file_path)

# 스크립트 실행
if __name__ == "__main__":
    asyncio.run(main())