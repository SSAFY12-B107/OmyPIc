# services/user.py
from typing import List, Optional, Dict, Any
from db.mongodb import get_mongodb
from bson import ObjectId
from datetime import date, datetime

async def create_user(
    name: str,
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

async def get_user_by_id(user_id: ObjectId) -> Optional[Dict]:
    db = await get_mongodb()
    users_collection = db.users
    user = await users_collection.find_one({"_id": user_id})
    
    if user and "_id" in user:
        user["_id"] = str(user["_id"])  # ObjectId를 문자열로 변환
    
    return user


async def get_users(skip: int = 0, limit: int = 10) -> List[Dict]:
    """
    사용자 목록 조회
    """
    db = await get_mongodb()
    users_collection = db.users
    users = []
    cursor = users_collection.find().skip(skip).limit(limit)
    async for document in cursor:
        document["_id"] = str(document["_id"])  # ObjectId를 문자열로 변환
        users.append(document)
    return users

async def update_user(user_id: ObjectId, update_data: Dict[str, Any]) -> Optional[Dict]:
    """
    사용자 정보 업데이트
    """
    db = await get_mongodb()
    users_collection = db.users
    
    # 사용자 존재 여부 확인
    user = await get_user_by_id(user_id)
    if not user:
        return None
    
    # 백그라운드 서베이 업데이트 처리
    if "background_survey" in update_data:
        # 기존 백그라운드 서베이 가져오기
        bg_survey = user.get("background_survey", {})
        # 새 백그라운드 서베이 데이터
        new_bg_survey = update_data.pop("background_survey", {})
        # 새 데이터를 기존 데이터에 병합
        if new_bg_survey:
            for key, value in new_bg_survey.items():
                if value is not None:  # None이 아닌 값만 업데이트
                    bg_survey[key] = value
            # 병합된 백그라운드 서베이를 업데이트 데이터에 추가
            update_data["background_survey"] = bg_survey
    
    # 업데이트 실행 (None이 아닌 값만)
    update_dict = {k: v for k, v in update_data.items() if v is not None}
    if update_dict:
        await users_collection.update_one(
            {"_id": user_id},
            {"$set": update_dict}
        )
    
    # 업데이트된 사용자 조회
    updated_user = await users_collection.find_one({"_id": user_id})
    return updated_user

async def delete_user(user_id: ObjectId) -> bool:
    """
    사용자 삭제
    """
    db = await get_mongodb()
    users_collection = db.users
    result = await users_collection.delete_one({"_id": user_id})
    return result.deleted_count > 0

def _convert_objectid_to_str(data):
    """MongoDB ObjectId를 문자열로 변환"""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "_id" and isinstance(value, ObjectId):
                data[key] = str(value)
            elif isinstance(value, dict) or isinstance(value, list):
                data[key] = _convert_objectid_to_str(value)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = _convert_objectid_to_str(item)
    return data

# 그리고 모든 서비스 함수에서 이 함수를 사용
async def get_user_by_id(user_id: ObjectId) -> Optional[Dict]:
    db = await get_mongodb()
    users_collection = db.users
    user = await users_collection.find_one({"_id": user_id})
    return _convert_objectid_to_str(user)