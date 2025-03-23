import sys
import os

# 현재 스크립트의 경로를 가져옴
current_path = os.path.dirname(os.path.abspath(__file__))
# Backend 디렉토리 경로 설정
backend_path = os.path.dirname(current_path)
# Backend 디렉토리를 Python 경로에 추가
sys.path.insert(0, backend_path)

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
import logging
from datetime import datetime

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_user_model():
    """
    기존 사용자 모델에 test_limits 필드를 추가하는 마이그레이션 스크립트
    """
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    logger.info(f"MongoDB에 연결됨: {settings.MONGODB_URL}, DB: {settings.MONGODB_DB_NAME}")
    logger.info("사용자 모델 마이그레이션 시작...")
    
    # test_limits 필드가 없는 사용자 찾기
    count = await db.users.count_documents({"test_limits": {"$exists": False}})
    logger.info(f"마이그레이션할 사용자 수: {count}")
    
    if count > 0:
        # 기본 test_limits 필드 추가
        result = await db.users.update_many(
            {"test_limits": {"$exists": False}},
            {"$set": {
                "test_limits": {
                    "test_count": 0,
                    "random_problem": 0
                }
            }}
        )
        
        logger.info(f"마이그레이션 완료: {result.modified_count}개 문서 업데이트됨")
    
    # 현재 테스트 상태를 기반으로 카운트 업데이트
    logger.info("사용자별 테스트 사용 횟수 계산 중...")
    
    # 모든 사용자 가져오기
    users = await db.users.find().to_list(length=None)
    
    for user in users:
        user_id = user["_id"]
        
        # short_test(0) 수 집계
        short_test_count = await db.tests.count_documents({
            "user_id": str(user_id),
            "test_type": False  # test_type 0 (False)
        })
        
        # full_test(1) 수 집계
        full_test_count = await db.tests.count_documents({
            "user_id": str(user_id),
            "test_type": True  # test_type 1 (True)
        })
        
        # 총 테스트 횟수 계산 (7문제 + 15문제)
        total_test_count = short_test_count + full_test_count
        
        # 테스트 횟수 업데이트 (기존 값과 새로 계산한 값 중 더 큰 값으로 설정)
        current_limits = user.get("test_limits", {"test_count": 0, "random_problem": 0})
        
        new_test_count = min(total_test_count, 3)  # 최대 3회로 제한
        
        await db.users.update_one(
            {"_id": user_id},
            {"$set": {
                "test_limits.test_count": new_test_count,
                "updated_at": datetime.now()
            }}
        )
        
        logger.info(f"사용자 {user_id}: 총 테스트={new_test_count}회 (7문제: {short_test_count}회, 15문제: {full_test_count}회) 업데이트됨")
    
    logger.info(f"총 {len(users)}명의 사용자 테스트 횟수 업데이트 완료")
    client.close()

if __name__ == "__main__":
    logger.info("사용자 모델 마이그레이션 스크립트 실행...")
    asyncio.run(migrate_user_model())
    logger.info("마이그레이션 완료!")