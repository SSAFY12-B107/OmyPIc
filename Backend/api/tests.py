from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.mongodb import get_mongodb
from datetime import datetime
from models.test import TestModel
from schemas.test import TestCreate, TestUpdate

router = APIRouter()

# 테스트 생성 엔드포인트
@router.post("/tests/", response_model=TestModel)
async def create_test(test_data: TestCreate, db: AsyncIOMotorDatabase = Depends(get_mongodb)):
    try:
        # 사용자 ID 문자열을 ObjectId로 변환
        user_id_obj = ObjectId(test_data.user_id)
    except:
        raise HTTPException(status_code=400, detail="유효하지 않은 사용자 ID 형식입니다")
    
    # 데이터베이스에 저장할 문서 준비
    test_dict = {
        "test_type": test_data.test_type,
        "user_id": user_id_obj,  # ObjectId로 변환하여 저장
        "test_date": datetime.now(),
        "problem_data": {}
    }
    
    # 데이터베이스에 저장
    result = await db.tests.insert_one(test_dict)
    
    # 저장된 문서 조회
    created_test = await db.tests.find_one({"_id": result.inserted_id})
    
    # ObjectId를 문자열로 변환
    if created_test:
        created_test["_id"] = str(created_test["_id"])
        created_test["user_id"] = str(created_test["user_id"])
        return created_test
    
    raise HTTPException(status_code=500, detail="테스트 생성 후 조회 실패")