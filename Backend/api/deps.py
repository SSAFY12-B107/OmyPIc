# Backend/api/deps.py
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.mongodb import get_mongodb
from bson import ObjectId

from jose import JWTError, jwt
from models.user import User
from typing import Dict, Any
from services import auth as auth_service
from itertools import cycle
from core.config import settings

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_mongodb)
) -> User:
    """
    프론트엔드에서 전달받은 액세스 토큰으로 현재 사용자 정보를 가져오는 의존성 함수
    """
    try:
        # 토큰 검증
        payload = jwt.decode(
            credentials.credentials, 
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 정보",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # MongoDB에서 사용자 조회
        user_data = await db.users.find_one({"_id": ObjectId(user_id)})
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
            
        return User(**user_data)
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 만료되었거나 유효하지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )


# OAuth2 스키마 설정
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
#     """
#     현재 인증된 사용자 정보 가져오기 (필수)
#     """
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="인증이 필요합니다",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
        
#     return await get_current_user(token)


# async def get_current_user_id_from_token(token: str = Depends(oauth2_scheme)) -> str:
#     """
#     현재 인증된 사용자 ID 가져오기
#     """
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="인증이 필요합니다",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     user = await auth_service.get_current_user(token)
#     return user["_id"]  # 사용자 ID 반환


# API 키 순환자 초기화
_gemini_key_cycle = None
_groq_key_cycle = None

def _init_key_cycles():
    global _gemini_key_cycle, _groq_key_cycle
    
    # 메서드 호출하여 실제 리스트 받기
    gemini_keys = settings.gemini_api_keys()  # 메서드 호출 추가
    groq_keys = settings.groq_api_keys()      # 메서드 호출 추가
    
    # 순환자 생성
    _gemini_key_cycle = cycle(gemini_keys) if gemini_keys else None
    _groq_key_cycle = cycle(groq_keys) if groq_keys else None

# 초기화 실행
_init_key_cycles()

def get_next_gemini_key():
    """다음 Gemini API 키를 반환합니다."""
    if _gemini_key_cycle is None:
        return ""
    return next(_gemini_key_cycle)

def get_next_groq_key():
    """다음 Groq API 키를 반환합니다."""
    if _groq_key_cycle is None:
        return ""
    return next(_groq_key_cycle)