from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

mongo_db = MongoDB()

def _init_db():
    """동기적으로 MongoDB에 연결 (임시 해결책)"""
    if mongo_db.db is None:
        try:
            mongo_db.client = AsyncIOMotorClient(settings.MONGODB_URL)
            mongo_db.db = mongo_db.client[settings.MONGODB_DB_NAME]
            print(f"MongoDB에 연결됨: {settings.MONGODB_URL}, DB: {settings.MONGODB_DB_NAME}")
        except Exception as e:
            print(f"MongoDB 연결 오류: {str(e)}")
            raise

async def connect_to_mongo():
    """MongoDB 연결 설정"""
    try:
        mongo_db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongo_db.db = mongo_db.client[settings.MONGODB_DB_NAME]
        logger.info("Connected to MongoDB: %s, DB: %s", settings.MONGODB_URL, settings.MONGODB_DB_NAME)
        print("Connected to MongoDB")
    except Exception as e:
        logger.error("MongoDB 연결 오류: %s", str(e))
        print(f"MongoDB 연결 오류: {str(e)}")
        raise

async def close_mongo_connection():
    """MongoDB 연결 종료"""
    if mongo_db.client:
        mongo_db.client.close()
        logger.info("MongoDB connection closed")
        print("MongoDB connection closed")

def get_collection(collection_name: str):
    """특정 컬렉션 가져오기"""
    if mongo_db.db is None:
        # 동기적으로 연결 시도
        _init_db()
    
    return mongo_db.db[collection_name]

# 초기 연결 설정 (개발 환경용)
_init_db()