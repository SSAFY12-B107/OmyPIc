from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

mongo_db = MongoDB()

async def connect_to_mongo():
    """MongoDB 연결 설정"""
    mongo_db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    mongo_db.db = mongo_db.client[settings.MONGODB_DB_NAME]
    print("Connected to MongoDB")

async def close_mongo_connection():
    """MongoDB 연결 종료"""
    if mongo_db.client:
        mongo_db.client.close()
        print("MongoDB connection closed")