from motor.motor_asyncio import AsyncIOMotorClient
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