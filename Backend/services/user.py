from typing import List, Optional, Dict, Any
from db.mongodb import get_collection
from models.user import User
from datetime import date, datetime
from bson import ObjectId

# 사용자 컬렉션 가져오기
async def get_users_collection():
    return await get_collection("users")

async def create_user(
    name: str,
    auth_provider: str = "local",
    current_opic_score: Optional[str] = None,
    target_opic_score: Optional[str] = None,
    target_exam_date: Optional[date] = None,
    background_survey: Optional[Dict] = None
) -> Dict:
    """새 사용자를 생성합니다."""
    users_collection = await get_users_collection()
    
    # 백그라운드 서베이 데이터 처리
    bg_survey = {}
    if background_survey:
        bg_survey = background_survey
    
    # date 객체를 datetime 객체로 변환 (MongoDB 호환성을 위해)
    converted_target_exam_date = None
    if target_exam_date:
        converted_target_exam_date = datetime.combine(target_exam_date, datetime.min.time())
    
    # 사용자 문서 생성
    user_doc = User.create_user_document(
        name=name,
        auth_provider=auth_provider,
        current_opic_score=current_opic_score,
        target_opic_score=target_opic_score,
        target_exam_date=converted_target_exam_date,  # 변환된 datetime 사용
        profession=bg_survey.get("profession"),
        is_student=bg_survey.get("is_student"),
        studied_lecture=bg_survey.get("studied_lecture"),
        living_place=bg_survey.get("living_place"),
        info=bg_survey.get("info")
    )
    
    # MongoDB에 사용자 추가
    result = await users_collection.insert_one(user_doc)
    
    # 생성된 사용자 정보 반환
    user = await users_collection.find_one({"_id": result.inserted_id})
    user["_id"] = str(user["_id"])  # ObjectId를 문자열로 변환
    return user

async def get_user_by_id(id: str) -> Optional[Dict]:
    """ID로 사용자를 조회합니다."""
    users_collection = await get_users_collection()
    try:
        object_id = ObjectId(id)
        user = await users_collection.find_one({"_id": object_id})
        if user:
            user["_id"] = str(user["_id"])  # ObjectId를 문자열로 변환
        return user
    except:
        return None

async def get_user_by_email(email: str) -> Optional[Dict]:
    """이메일로 사용자를 조회합니다."""
    users_collection = await get_users_collection()
    user = await users_collection.find_one({"background_survey.email": email})
    if user:
        user["_id"] = str(user["_id"])  # ObjectId를 문자열로 변환
    return user

async def get_users(skip: int = 0, limit: int = 10) -> List[Dict]:
    """모든 사용자를 조회합니다."""
    users_collection = await get_users_collection()
    users = []
    cursor = users_collection.find().skip(skip).limit(limit)
    async for document in cursor:
        document["_id"] = str(document["_id"])  # ObjectId를 문자열로 변환
        users.append(document)
    return users

async def update_user(id: str, update_data: Dict[str, Any]) -> Optional[Dict]:
    """사용자 정보를 업데이트합니다."""
    users_collection = await get_users_collection()
    
    try:
        object_id = ObjectId(id)
        
        # 사용자 존재 여부 확인
        user = await users_collection.find_one({"_id": object_id})
        if not user:
            return None
        
        # 백그라운드 서베이 데이터 처리
        if "background_survey" in update_data:
            bg_survey = user.get("background_survey", {})
            new_bg_survey = update_data.pop("background_survey", {})
            
            if new_bg_survey:
                if bg_survey is None:
                    bg_survey = {}
                
                for key, value in new_bg_survey.items():
                    if value is not None:
                        bg_survey[key] = value
                
                update_data["background_survey"] = bg_survey
        
        # date 객체를 datetime 객체로 변환 (MongoDB 호환성을 위해)
        if "target_exam_date" in update_data and isinstance(update_data["target_exam_date"], date):
            update_data["target_exam_date"] = datetime.combine(
                update_data["target_exam_date"], 
                datetime.min.time()
            )
        
        # 업데이트할 필드 필터링
        update_dict = {k: v for k, v in update_data.items() if v is not None}
        update_dict["updated_at"] = datetime.now()
        
        if update_dict:
            await users_collection.update_one(
                {"_id": object_id},
                {"$set": update_dict}
            )
        
        # 업데이트된 사용자 정보 반환
        updated_user = await users_collection.find_one({"_id": object_id})
        updated_user["_id"] = str(updated_user["_id"])  # ObjectId를 문자열로 변환
        return updated_user
    except:
        return None

async def delete_user(id: str) -> bool:
    """사용자를 삭제합니다."""
    users_collection = await get_users_collection()
    try:
        object_id = ObjectId(id)
        result = await users_collection.delete_one({"_id": object_id})
        return result.deleted_count > 0
    except:
        return False
