#!/usr/bin/env python3
"""
User 모델의 limits 필드에 categorical_test_limit 필드를 추가하는 스크립트.
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("user-migration")

async def add_categorical_limit():
    """User 모델의 limits 필드에 categorical_test_limit 필드를 추가하는 함수"""
    logger.info("사용자 limits 필드에 categorical_test_limit 추가 시작")
    
    # MongoDB 연결
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    users_collection = db.users
    
    try:
        # 이미 categorical_test_limit 필드가 없는 사용자만 찾기
        query = {"limits.categorical_test_limit": {"$exists": False}}
        count = await users_collection.count_documents(query)
        
        if count == 0:
            logger.info("모든 사용자가 이미 categorical_test_limit 필드를 가지고 있습니다.")
            return
            
        logger.info(f"{count}명의 사용자에게 categorical_test_limit 필드 추가 시작")
        
        # 필드 추가
        result = await users_collection.update_many(
            query,
            {"$set": {"limits.categorical_test_limit": 0}}
        )
        
        logger.info(f"총 {result.modified_count}명의 사용자에게 필드 추가 완료")
        
        # 필드가 없는 사용자 확인
        remaining = await users_collection.count_documents(query)
        if remaining > 0:
            logger.warning(f"여전히 {remaining}명의 사용자에게 필드가 추가되지 않았습니다.")
        else:
            logger.info("모든 사용자에게 필드 추가 완료")
        
    except Exception as e:
        logger.error(f"필드 추가 중 오류 발생: {str(e)}")
    finally:
        # 연결 종료
        client.close()
        logger.info("MongoDB 연결 종료")

if __name__ == "__main__":
    asyncio.run(add_categorical_limit())