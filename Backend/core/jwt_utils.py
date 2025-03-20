# Backend/core/jwt_utils.py
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from core.config import settings

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    액세스 토큰 생성
    """
    to_encode = data.copy()
    
    # 만료 시간 설정
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 클레임 추가
    to_encode.update({"exp": expire, "type": "access"})
    
    # 토큰 생성
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """
    리프레시 토큰 생성
    """
    to_encode = data.copy()
    
    # 리프레시 토큰은 더 긴 유효 기간을 가짐
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # 클레임 추가
    to_encode.update({"exp": expire, "type": "refresh"})
    
    # 토큰 생성
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

def decode_jwt(token: str) -> dict:
    """
    JWT 토큰 디코딩 및 페이로드 반환
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"유효하지 않은 토큰입니다: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )