# from typing import List, Optional, Dict, Any
# from db.mongodb import get_collection
# from Backend.models.user import User
# from datetime import date

# # 사용자 컬렉션 가져오기
# users_collection = get_collection("users")

# async def get_next_user_id() -> int:
#     """
#     사용자 ID 자동 증가 로직
#     """
#     # 가장 큰 user_id 조회
#     result = await users_collection.find_one(
#         sort=[("user_id", -1)]
#     )
    
#     # 결과가 없으면 1부터 시작, 있으면 최대값 + 1
#     if result is None or "user_id" not in result:
#         return 1
#     return result["user_id"] + 1

# async def create_user(
#     name: str,
#     auth_provider: str = "local",
#     current_opic_score: Optional[str] = None,
#     target_opic_score: Optional[str] = None,
#     target_exam_date: Optional[date] = None,
#     background_survey: Optional[Dict] = None
# ) -> Dict:
#     """
#     새 사용자 생성
#     """
#     # 다음 user_id 가져오기
#     user_id = await get_next_user_id()
    
#     # 기본 백그라운드 서베이 정보
#     bg_survey = {}
#     if background_survey:
#         bg_survey = background_survey
    
#     # 사용자 문서 생성
#     user_doc = User.create_user_document(
#         user_id=user_id,
#         name=name,
#         auth_provider=auth_provider,
#         current_opic_score=current_opic_score,
#         target_opic_score=target_opic_score,
#         target_exam_date=target_exam_date,
#         profession=bg_survey.get("profession"),
#         is_student=bg_survey.get("is_student"),
#         studied_lecture=bg_survey.get("studied_lecture"),
#         living_place=bg_survey.get("living_place"),
#         info=bg_survey.get("info")
#     )
    
#     # MongoDB에 삽입
#     result = await users_collection.insert_one(user_doc)
    
#     # 삽입된 문서의 ID로 완전한 문서 조회
#     user = await users_collection.find_one({"_id": result.inserted_id})
#     return user

# async def get_user_by_id(user_id: int) -> Optional[Dict]:
#     """
#     사용자 ID로 사용자 조회
#     """
#     user = await users_collection.find_one({"user_id": user_id})
#     return user

# async def get_users(skip: int = 0, limit: int = 10) -> List[Dict]:
#     """
#     사용자 목록 조회
#     """
#     users = []
#     cursor = users_collection.find().skip(skip).limit(limit)
#     async for document in cursor:
#         users.append(document)
#     return users

# async def update_user(user_id: int, update_data: Dict[str, Any]) -> Optional[Dict]:
#     """
#     사용자 정보 업데이트
#     """
#     # 사용자 존재 여부 확인
#     user = await get_user_by_id(user_id)
#     if not user:
#         return None
    
#     # 백그라운드 서베이 업데이트 처리
#     if "background_survey" in update_data:
#         # 기존 백그라운드 서베이 정보 가져오기
#         bg_survey = user.get("background_survey", {})
#         # 업데이트할 백그라운드 서베이 정보
#         new_bg_survey = update_data.pop("background_survey", {})
#         # 기존 정보에 새 정보 병합
#         if new_bg_survey:
#             for key, value in new_bg_survey.items():
#                 if value is not None:  # None이 아닌 값만 업데이트
#                     bg_survey[key] = value
#             # 업데이트 데이터에 병합된 백그라운드 서베이 추가
#             update_data["background_survey"] = bg_survey
    
#     # 업데이트 실행 (None이 아닌 값만 업데이트)
#     update_dict = {k: v for k, v in update_data.items() if v is not None}
#     if update_dict:
#         await users_collection.update_one(
#             {"user_id": user_id},
#             {"$set": update_dict}
#         )
    
#     # 업데이트된 사용자 조회
#     updated_user = await users_collection.find_one({"user_id": user_id})
#     return updated_user

# async def delete_user(user_id: int) -> bool:
#     """
#     사용자 삭제
#     """
#     result = await users_collection.delete_one({"user_id": user_id})
#     return result.deleted_count > 0