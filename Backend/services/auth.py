# Backend/services/auth.py
from typing import Dict, Optional, Any
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from core.config import settings
from core.jwt_utils import decode_jwt


async def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    액세스 토큰 생성
    """
    to_encode = data.copy()
    
    # 만료 시간 설정
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # JWT 토큰 생성
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

async def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    리프레시 토큰 생성
    """
    to_encode = data.copy()
    
    # 만료 시간 설정 (리프레시 토큰 - 일반적으로 더 긴 만료 시간)
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    
    # JWT 토큰 생성
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_REFRESH_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

async def refresh_access_token(refresh_token: str) -> Dict[str, str]:
    """
    리프레시 토큰으로 새 액세스 토큰 발급
    """
    try:
        # 리프레시 토큰 검증
        payload = decode_jwt(refresh_token, settings.JWT_REFRESH_SECRET_KEY)
        
        # 사용자 정보 추출
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 리프레시 토큰"
            )
        
        # 새 액세스 토큰 발급
        access_token = await create_access_token({"sub": user_id})
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="리프레시 토큰이 만료되었습니다"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰"
        )