#!/usr/bin/env python3
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB 연결 정보 - 실제 환경에 맞게 수정하세요
MONGODB_URL = "mongodb+srv://S12P22B107:tgXSWypINd@ssafy.ngivl.mongodb.net/S12P22B107?authSource=admin"
MONGODB_DB_NAME = "S12P22B107"

# 변경할 카테고리 매핑
CATEGORY_MAPPING = {
    "모임/축하": "모임축하",
    "예약/약속": "예약약속",
    "술집/바에 가기": "술집바에 가기",
    "식당/카페 가기": "식당카페 가기",
    "산업/회사": "산업회사",
    "하이킹, 트레킹": "하이킹트레킹",
    "공연/콘서트보기": "공연콘서트보기",
    "친구/가족": "친구가족"
}

async def update_topic_categories():
    # MongoDB 연결
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]
    collection = db.problems  # problem 컬렉션 접근
    
    logger.info("MongoDB에 연결되었습니다.")
    
    # 변경 전 카테고리 현황 조회
    before_stats = {}
    async for doc in collection.aggregate([
        {"$group": {"_id": "$topic_category", "count": {"$sum": 1}}}
    ]):
        before_stats[doc["_id"]] = doc["count"]
    
    logger.info("변경 전 카테고리 현황:")
    for category, count in before_stats.items():
        logger.info(f"  - {category}: {count}개 문제")
    
    # 각 카테고리별로 업데이트 수행
    total_updated = 0
    for old_category, new_category in CATEGORY_MAPPING.items():
        result = await collection.update_many(
            {"topic_category": old_category},
            {"$set": {"topic_category": new_category}}
        )
        
        if result.modified_count > 0:
            logger.info(f"'{old_category}' → '{new_category}'로 {result.modified_count}개 문제 업데이트 완료")
            total_updated += result.modified_count
    
    # 변경 후 카테고리 현황 조회
    after_stats = {}
    async for doc in collection.aggregate([
        {"$group": {"_id": "$topic_category", "count": {"$sum": 1}}}
    ]):
        after_stats[doc["_id"]] = doc["count"]
    
    logger.info("변경 후 카테고리 현황:")
    for category, count in after_stats.items():
        logger.info(f"  - {category}: {count}개 문제")
    
    logger.info(f"총 {total_updated}개 문제의 topic_category가 업데이트되었습니다.")
    
    # 연결 종료
    client.close()

async def main():
    try:
        logger.info("topic_category 값 업데이트를 시작합니다...")
        await update_topic_categories()
        logger.info("모든 업데이트가 성공적으로 완료되었습니다.")
    except Exception as e:
        logger.error(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())