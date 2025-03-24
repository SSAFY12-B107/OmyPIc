# Backend/api/deps.py
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.mongodb import get_mongodb
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

from jose import JWTError, jwt
from models.user import User
from typing import Dict, Any
from services import auth as auth_service
from itertools import cycle
from core.config import settings
import logging


# 로거 설정
logger = logging.getLogger(__name__)

# HTTP Bearer 토큰 인증 객체 생성
security = HTTPBearer(auto_error=False)

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
        
        logger.info(f"JWT 페이로드: {payload}")
        
        user_id = payload.get("sub")
        logger.info(f"추출된 사용자 ID: {user_id}, 타입: {type(user_id)}")
        
        if user_id is None:
            logger.warning("토큰에 사용자 ID(sub)가 없습니다")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 정보",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 사용자 조회 (ObjectId 또는 문자열 ID로)
        users_collection = db["users"]
        user_data = None
        
        # 방법 1: ObjectId로 조회 시도
        try:
            object_id = ObjectId(user_id)
            logger.info(f"ObjectId 변환 성공: {object_id}")
            user_data = await users_collection.find_one({"_id": object_id})
        except InvalidId:
            logger.warning(f"ObjectId 변환 실패: {user_id}")
            # ObjectId 변환 실패 시 문자열 ID로 시도하지 않고 오류 발생
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않은 사용자 ID 형식입니다."
            )
        
        if user_data is None:
            logger.warning(f"사용자를 찾을 수 없음: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
            
        # User.from_mongo 메서드 활용
        logger.info("User.from_mongo 메서드로 사용자 객체 생성")
        user = User.from_mongo(user_data)
        logger.info(f"사용자 인증 완료: {user.name}")
        return user
        
    except JWTError as e:
        # 오류 메시지 개선
        error_msg = str(e)
        if "expired" in error_msg.lower():
            logger.error(f"JWT 토큰 만료: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증 토큰이 만료되었습니다. 다시 로그인하거나 토큰을 갱신하세요.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            logger.error(f"JWT 디코딩 오류: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 토큰입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        logger.error(f"인증 과정에서 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다"
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