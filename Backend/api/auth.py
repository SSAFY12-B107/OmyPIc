from fastapi import APIRouter, HTTPException, status, Depends, Body
# from fastapi.security import OAuth2PasswordBearer
# from typing import Dict, Any, Optional
# from datetime import datetime, timedelta
# # from jose import jwt, JWTError
# from pydantic import BaseModel
# from db.mongodb import get_collection
# from core.config import settings
# from services import user as user_service
# import httpx

router = APIRouter()

# # OAuth2 토큰 스키마
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# # 구글 로그인 요청 모델
# class GoogleLoginRequest(BaseModel):
#     id_token: str

# # 백그라운드 서베이 요청 모델
# class BackgroundSurveyRequest(BaseModel):
#     profession: Optional[int] = None
#     is_student: Optional[bool] = None
#     studied_lecture: Optional[int] = None
#     living_place: Optional[int] = None
#     info: Optional[list[str]] = None

# # JWT 토큰 생성 함수
# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
#     return encoded_jwt

# # 현재 사용자 가져오기
# async def get_current_user(token: str = Depends(oauth2_scheme)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="인증 정보가 유효하지 않습니다",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         user_id: str = payload.get("sub")
#         if user_id is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception
    
#     user = await user_service.get_user_by_id(user_id)
#     if user is None:
#         raise credentials_exception
#     return user

# @router.post("/google/login")
# async def google_login(request: GoogleLoginRequest):
#     """
#     구글 소셜 로그인 처리
#     """
#     try:
#         # 구글 ID 토큰 검증
#         async with httpx.AsyncClient() as client:
#             response = await client.get(
#                 f"https://oauth2.googleapis.com/tokeninfo?id_token={request.id_token}"
#             )
#             if response.status_code != 200:
#                 raise HTTPException(
#                     status_code=status.HTTP_401_UNAUTHORIZED,
#                     detail="구글 인증에 실패했습니다"
#                 )
            
#             user_info = response.json()
#             email = user_info.get("email")
#             name = user_info.get("name")
#             picture = user_info.get("picture")
            
#             # 사용자 정보 저장 또는 업데이트
#             user = await user_service.get_user_by_email(email)
            
#             if not user:
#                 # 새 사용자 생성
#                 user = await user_service.create_user(
#                     name=name,
#                     auth_provider="google",
#                     background_survey={
#                         "profile_image": picture,
#                         "email": email
#                     }
#                 )
#                 user_id = user["_id"]
#             else:
#                 # 기존 사용자 업데이트
#                 user_id = user["_id"]
#                 await user_service.update_user(
#                     id=user_id,
#                     update_data={
#                         "name": name,
#                         "auth_provider": "google",
#                         "background_survey": {
#                             "profile_image": picture,
#                             "email": email
#                         }
#                     }
#                 )
#                 user = await user_service.get_user_by_id(user_id)
            
#             # JWT 토큰 생성
#             access_token = create_access_token(
#                 data={"sub": user_id, "email": email}
#             )
            
#             return {
#                 "status": "success",
#                 "message": "구글 로그인 성공",
#                 "data": {
#                     "access_token": access_token,
#                     "token_type": "bearer",
#                     "user": user
#                 }
#             }
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"로그인 중 오류가 발생했습니다: {str(e)}"
#         )

# @router.patch("/background-survey")
# async def background_survey(
#     survey_data: BackgroundSurveyRequest,
#     current_user: dict = Depends(get_current_user)
# ):
#     """
#     백그라운드 서베이 정보 업데이트
#     """
#     try:
#         user_id = current_user["_id"]
        
#         # 서베이 데이터 업데이트
#         update_data = {"background_survey": survey_data.dict(exclude_unset=True)}
        
#         updated_user = await user_service.update_user(user_id, update_data)
#         if not updated_user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="사용자를 찾을 수 없습니다"
#             )
        
#         return {
#             "status": "success",
#             "message": "백그라운드 서베이 정보가 업데이트되었습니다",
#             "data": updated_user
#         }
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"서베이 정보 업데이트 중 오류가 발생했습니다: {str(e)}"
#         )

# @router.post("/logout")
# async def logout(current_user: dict = Depends(get_current_user)):
#     """
#     로그아웃 처리
    
#     참고: JWT는 서버 측에서 무효화할 수 없으므로, 클라이언트에서 토큰을 삭제하는 것이 일반적입니다.
#     필요에 따라 토큰 블랙리스트를 구현할 수 있습니다.
#     """
#     return {
#         "status": "success",
#         "message": "로그아웃 성공"
#     }
