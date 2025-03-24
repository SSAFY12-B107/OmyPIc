# scripts/change_limt_field.py
import asyncio
import logging
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_mongodb():
    """MongoDB 연결"""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    return client[settings.MONGODB_DB_NAME]

async def migrate_test_limits_to_limits():
    """test_limits 필드를 limits 필드로 마이그레이션"""
    logger.info("마이그레이션 시작: test_limits → limits")
    
    # DB 연결
    db = await get_mongodb()
    
    # 전체 사용자 수 확인
    total_users = await db.users.count_documents({})
    logger.info(f"전체 사용자 수: {total_users}")
    
    # test_limits 필드가 있는 사용자 수 확인
    users_with_test_limits = await db.users.count_documents({"test_limits": {"$exists": True}})
    logger.info(f"test_limits 필드가 있는 사용자 수: {users_with_test_limits}")
    
    # limits 필드가 있는 사용자 수 확인
    users_with_limits = await db.users.count_documents({"limits": {"$exists": True}})
    logger.info(f"limits 필드가 있는 사용자 수: {users_with_limits}")
    
    # 마이그레이션이 필요한 사용자 조회
    cursor = db.users.find({"test_limits": {"$exists": True}})
    
    count_migrated = 0
    count_skipped = 0
    count_failed = 0
    
    async for user in cursor:
        user_id = str(user["_id"])
        try:
            # test_limits 필드가 있는 경우
            if "test_limits" in user:
                test_limits = user["test_limits"]
                
                # 이미 limits 필드가 있는 경우 건너뛰기 (중복 마이그레이션 방지)
                if "limits" in user:
                    logger.warning(f"사용자 {user_id}는 이미 limits 필드가 있어 건너뜁니다.")
                    count_skipped += 1
                    continue
                
                # script_count가 없으면 추가
                if "script_count" not in test_limits:
                    test_limits["script_count"] = 0
                
                # 업데이트 수행
                result = await db.users.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {"limits": test_limits},
                        "$unset": {"test_limits": ""}
                    }
                )
                
                if result.modified_count > 0:
                    logger.info(f"사용자 {user_id} 마이그레이션 완료")
                    count_migrated += 1
                else:
                    logger.warning(f"사용자 {user_id} 마이그레이션 실패 - 수정된 내용 없음")
                    count_failed += 1
        except Exception as e:
            logger.error(f"사용자 {user_id} 마이그레이션 중 오류 발생: {str(e)}")
            count_failed += 1
    
    # 마이그레이션 이후 확인
    users_with_limits_after = await db.users.count_documents({"limits": {"$exists": True}})
    users_with_test_limits_after = await db.users.count_documents({"test_limits": {"$exists": True}})
    
    logger.info("마이그레이션 완료")
    logger.info(f"마이그레이션된 사용자 수: {count_migrated}")
    logger.info(f"건너뛴 사용자 수: {count_skipped}")
    logger.info(f"실패한 사용자 수: {count_failed}")
    logger.info(f"마이그레이션 후 limits 필드가 있는 사용자 수: {users_with_limits_after}")
    logger.info(f"마이그레이션 후 test_limits 필드가 있는 사용자 수: {users_with_test_limits_after}")
    
    # limits 필드가 없는 사용자에게 기본 limits 추가
    users_without_limits = await db.users.count_documents({"limits": {"$exists": False}})
    logger.info(f"limits 필드가 없는 사용자 수: {users_without_limits}")
    
    if users_without_limits > 0:
        logger.info("limits 필드가 없는 사용자에게 기본값 추가 시작")
        
        result = await db.users.update_many(
            {"limits": {"$exists": False}},
            {"$set": {"limits": {"test_count": 0, "random_problem": 0, "script_count": 0}}}
        )
        
        logger.info(f"기본 limits 추가 완료: {result.modified_count}명의 사용자 업데이트됨")

async def main():
    try:
        await migrate_test_limits_to_limits()
    except Exception as e:
        logger.error(f"마이그레이션 중 오류 발생: {str(e)}")
    finally:
        # 모터 클라이언트 연결 종료를 위한 지연
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())