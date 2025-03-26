# Backend/services/user.py
from typing import List, Optional, Dict, Any
from db.mongodb import get_mongodb
from bson import ObjectId
from datetime import date, datetime

async def create_user(
    name: str,
    auth_provider: str = "google",
    email: Optional[str] = None,
    provider_id: Optional[str] = None,
    profile_image: Optional[str] = None,
    current_opic_score: Optional[str] = None,
    target_opic_score: Optional[str] = None,
    target_exam_date: Optional[datetime] = None,
    is_onboarded: bool = False
) -> Dict:
    """
    새 사용자 생성
    
    Google 콜백 로직과 일관성을 유지하기 위해 수정됨
    """
    # MongoDB 데이터베이스 객체 가져오기
    db = await get_mongodb()
    
    # 현재 시간
    current_time = datetime.now()
    
    # 백그라운드 서베이 초기 설정
    background_survey = {
        "profession": 0,
        "is_student": False,
        "studied_lecture": 0,
        "living_place": 0,
        "info": []
    }
    
    # 평균 점수 초기화
    average_score = {
        "comboset_score": None,
        "roleplaying_score": None, 
        "total_score": None,
        "unexpected_score": None
    }
    
    # 테스트 제한 설정
    limits = {
        "script_count": 0,
        "test_count": 0,        # 기본 테스트 횟수
        "random_problem": 0     # 기본 랜덤 문제 수
    }
    
    # 사용자 문서 생성
    user_doc = {
        "name": name,
        "auth_provider": auth_provider,
        "email": email,
        "provider_id": provider_id,
        "profile_image": profile_image,
        "current_opic_score": current_opic_score,
        "target_opic_score": target_opic_score,
        "target_exam_date": target_exam_date,
        "is_onboarded": is_onboarded,
        "created_at": current_time,
        "updated_at": current_time,
        "background_survey": background_survey,
        "average_score": average_score,
        "limits": limits
    }
    
    # MongoDB에 사용자 추가
    result = await db.users.insert_one(user_doc)
    
    # 삽입된 ID로 전체 문서 검색
    user = await db.users.find_one({"_id": result.inserted_id})
    
    # ObjectId를 문자열로 명시적 변환
    if user and "_id" in user:
        user["_id"] = str(user["_id"])
    
    return user


async def get_user_by_email(email: str) -> Optional[Dict]:
    """
    이메일로 사용자 조회
    """
    db = await get_mongodb()
    users_collection = db.users
    
    user = await users_collection.find_one({"email": email})
    
    if user and "_id" in user:
        user["_id"] = str(user["_id"])  # ObjectId를 문자열로 변환
    
    return user

async def get_user_by_id(user_id: ObjectId) -> Optional[Dict]:
    """
    ID로 사용자 조회
    """
    db = await get_mongodb()
    users_collection = db.users
    
    user = await users_collection.find_one({"_id": user_id})
    
    if user and "_id" in user:
        user["_id"] = str(user["_id"])  # ObjectId를 문자열로 변환
    
    return user

async def get_users(skip: int = 0, limit: int = 10) -> List[Dict]:
    """
    모든 사용자 조회
    """
    db = await get_mongodb()
    users_collection = db.users
    
    cursor = users_collection.find().skip(skip).limit(limit)
    users = []
    
    async for user in cursor:
        user["_id"] = str(user["_id"])  # ObjectId를 문자열로 변환
        users.append(user)
    
    return users

async def update_user(user_id: ObjectId, update_data: Dict) -> Optional[Dict]:
    """
    사용자 정보 업데이트
    """
    db = await get_mongodb()
    users_collection = db.users
    
    # 업데이트할 필드 필터링 (None 값은 업데이트하지 않음)
    filtered_update = {k: v for k, v in update_data.items() if v is not None}
    
    if not filtered_update:
        # 업데이트할 데이터가 없으면 기존 사용자 반환
        return await get_user_by_id(user_id)
    
    # 업데이트 수행
    result = await users_collection.update_one(
        {"_id": user_id},
        {"$set": filtered_update}
    )
    
    if result.modified_count == 0 and result.matched_count == 0:
        # 문서가 존재하지 않음
        return None
    
    # 업데이트된 사용자 반환
    return await get_user_by_id(user_id)

async def delete_user(user_id: ObjectId) -> bool:
    """
    사용자 삭제
    """
    db = await get_mongodb()
    users_collection = db.users
    
    result = await users_collection.delete_one({"_id": user_id})
    
    # 삭제된 문서가 있는지 확인
    return result.deleted_count > 0