# Backend/services/user.py
from typing import List, Optional, Dict, Any
from db.mongodb import get_mongodb
from bson import ObjectId
from datetime import date, datetime

async def create_user(
    name: str,
    email: Optional[str] = None,  # 이메일 필드 추가
    auth_provider: str = "google",
    current_opic_score: Optional[str] = None,
    target_opic_score: Optional[str] = None,
    target_exam_date: Optional[date] = None,
    background_survey: Optional[Dict] = None
) -> Dict:
    """
    새 사용자 생성
    """
    # MongoDB 데이터베이스 객체 가져오기
    db = await get_mongodb()
    users_collection = db.users
    
    # 백그라운드 서베이 정보 준비
    bg_survey = background_survey or {
        "profession": None,
        "is_student": None,
        "studied_lecture": None,
        "living_place": None,
        "info": []
    }
    
    # date 객체를 datetime 객체로 변환 (MongoDB 호환성을 위해)
    converted_target_exam_date = None
    if target_exam_date:
        converted_target_exam_date = datetime.combine(target_exam_date, datetime.min.time())
    
    # 사용자 문서 생성
    user_doc = {
        "name": name,
        "email": email,  # 이메일 필드 추가
        "auth_provider": auth_provider,
        "current_opic_score": current_opic_score,
        "target_opic_score": target_opic_score,
        "target_exam_date": target_exam_date,
        "is_onboarded": False,
        "created_at": datetime.now(),
        "background_survey": bg_survey
    }
    
    # MongoDB에 사용자 추가
    result = await users_collection.insert_one(user_doc)
    
    # 삽입된 ID로 전체 문서 검색
    user = await users_collection.find_one({"_id": result.inserted_id})
    user["_id"] = str(user["_id"])  # ObjectId를 문자열로 변환
    return user

# 이메일로 사용자 조회 함수 추가
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

# 나머지 기존 함수들...
# get_user_by_id, get_users, update_user, delete_user 등 유지