from motor.motor_asyncio import AsyncIOMotorClient
import pymongo
from core.config import settings
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

mongo_db = MongoDB()


async def connect_to_mongo():
    """MongoDB 연결 설정"""
    try:
        mongo_db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongo_db.db = mongo_db.client[settings.MONGODB_DB_NAME]
        print("Connected to MongoDB")
    except Exception as e:
        print(f"MongoDB 연결 오류: {str(e)}")
        raise

async def close_mongo_connection():
    """MongoDB 연결 종료"""
    if mongo_db.client:
        mongo_db.client.close()
        print("MongoDB connection closed")

async def get_mongodb():
    """MongoDB 데이터베이스 세션 의존성"""
    return mongo_db.db

async def get_collection(collection_name: str):
    """
    MongoDB 컬렉션 가져오기
    """
    db = await get_mongodb()
    return db[collection_name]


_sync_client = None # 워커 프로세스당 클라이언트를 재사용하기 위한 변수 (선택적 개선)

def get_mongodb_sync():
    """
    MongoDB 데이터베이스 세션 함수 (동기 버전)
    Celery 작업용 - pymongo 사용
    """
    global _sync_client
    from core.config import settings

    # 워커 프로세스 내에서 클라이언트 인스턴스를 한 번만 생성하여 재사용 (권장)
    if _sync_client is None:
        try:
            # 동기 드라이버 pymongo 사용
            _sync_client = pymongo.MongoClient(settings.MONGODB_URL)
            # 연결 테스트 (선택 사항)
            _sync_client.admin.command('ping')
            logger.info("Successfully connected to MongoDB (sync) for Celery.")
        except pymongo.errors.ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB (sync): {e}", exc_info=True)
            # 연결 실패 시 None을 반환하거나 예외를 발생시켜 작업 실패 유도
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during sync MongoDB connection: {e}", exc_info=True)
            return None

    # 클라이언트가 성공적으로 생성되었는지 확인 후 DB 반환
    if _sync_client:
        try:
            # settings에서 올바른 DB 이름을 가져오는지 확인 중요!
            db = _sync_client[settings.MONGODB_DB_NAME]
            return db
        except Exception as e:
            logger.error(f"Failed to get database '{settings.MONGODB_DB_NAME}' from sync client: {e}", exc_info=True)
            return None
    else:
        # 클라이언트 생성 실패 시
        logger.error("Sync MongoDB client is not available.")
        return None