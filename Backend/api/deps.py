# Backend/api/deps.py
from fastapi import Depends, HTTPException, status, Cookie, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.mongodb import get_mongodb
from motor.motor_asyncio import AsyncIOMotorDatabase as Database
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
        
        # 사용자 조회
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user is None:
            logger.warning(f"사용자를 찾을 수 없음: {user_id}")
            # 상태 코드를 401에서 404로 변경
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return User.from_mongo(user)
        
    except jwt.JWTError:
        # 이 부분은 401 유지 (인증 실패)
        logger.error(f"JWT 토큰 검증 실패")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        # 이미 생성된 HTTPException은 그대로 전달
        raise
    except Exception as e:
        logger.error(f"인증 과정에서 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="인증 처리 중 오류가 발생했습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
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

async def get_current_user_for_multipart(
    request: Request,
    db: Database = Depends(get_mongodb)
) -> User:
    """파일 업로드 요청에서 사용자 인증을 처리합니다."""
    try:
        # 헤더에서 Authorization 토큰 추출 시도
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # Bearer 토큰 추출
            try:
                scheme, token = auth_header.split()
                if scheme.lower() != "bearer":
                    raise HTTPException(status_code=401, detail="Bearer 형식의 토큰이 필요합니다")
                
                # 토큰 검증
                payload = jwt.decode(
                    token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
                )
                user_id = payload.get("sub")
                
                if not user_id:
                    raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")
                
                # 사용자 조회
                user = await db.users.find_one({"_id": ObjectId(user_id)})
                if not user:
                    raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
                
                return User.from_mongo(user)
            except ValueError:
                # Authorization 헤더가 "Bearer 토큰" 형식이 아닌 경우
                raise HTTPException(status_code=401, detail="잘못된 인증 형식입니다")
            except jwt.JWTError:
                # 토큰 검증 실패
                raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")
        
        # 폼 데이터에서 user_id 추출 시도
        form = await request.form()
        if "user_id" not in form:
            raise HTTPException(status_code=401, detail="인증 정보가 필요합니다")
        
        user_id = form.get("user_id")
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="유효하지 않은 사용자 ID 형식입니다")
        
        # 사용자 조회
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        return User.from_mongo(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인증 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=401, detail="인증에 실패했습니다")

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