# app/services/auth.py
from datetime import datetime, timedelta
import time
import base64
import hmac
import hashlib
import secrets
import jwt
from fastapi import HTTPException, status
from typing import Dict, Optional

from core.config import settings

def create_csrf_token() -> str:
    """
    서명된 CSRF 토큰 생성
    
    토큰은 타임스탬프와 랜덤 데이터로 구성되며 HMAC으로 서명됩니다.
    서버에 토큰을 저장하지 않고도 검증할 수 있습니다.
    
    Returns:
        str: 서명된 CSRF 토큰
    """
    # 현재 타임스탬프
    timestamp = int(time.time())
    
    # 랜덤 데이터
    random_data = secrets.token_urlsafe(16)
    
    # 토큰 데이터: timestamp:random_data
    token_data = f"{timestamp}:{random_data}"
    
    # HMAC-SHA256 서명 생성
    signature = hmac.new(
        settings.JWT_SECRET_KEY.encode(),
        token_data.encode(),
        hashlib.sha256
    ).digest()
    
    # Base64 인코딩된 서명
    b64_signature = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    # 최종 토큰: data.signature
    token = f"{token_data}.{b64_signature}"
    
    return token

def verify_csrf_token(token: str, max_age: int = 3600) -> bool:
    """
    서명된 CSRF 토큰 검증
    
    Args:
        token (str): 검증할 CSRF 토큰
        max_age (int): 토큰의 최대 유효 시간(초), 기본값 1시간
        
    Returns:
        bool: 토큰 유효성 여부
        
    Raises:
        HTTPException: 토큰이 유효하지 않을 경우
    """
    try:
        # 토큰 파싱
        token_parts = token.split('.')
        if len(token_parts) != 2:
            raise ValueError("잘못된 토큰 형식입니다")
        
        token_data, provided_signature = token_parts
        
        # 타임스탬프 추출 및 검증
        timestamp_str, _ = token_data.split(':')
        timestamp = int(timestamp_str)
        
        # 토큰 만료 확인
        current_time = int(time.time())
        if current_time - timestamp > max_age:
            raise ValueError("토큰이 만료되었습니다")
        
        # 서명 재생성하여 검증
        expected_signature = hmac.new(
            settings.JWT_SECRET_KEY.encode(),
            token_data.encode(),
            hashlib.sha256
        ).digest()
        
        expected_b64 = base64.urlsafe_b64encode(expected_signature).decode('utf-8').rstrip('=')
        
        # 안전한 비교 (타이밍 공격 방지)
        if not hmac.compare_digest(expected_b64, provided_signature):
            raise ValueError("유효하지 않은 서명입니다")
        
        return True
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"유효하지 않거나 만료된 CSRF 토큰: {str(e)}"
        )

def create_access_token(data: dict) -> str:
    """
    JWT 액세스 토큰 생성
    
    Args:
        data (dict): 토큰에 인코딩할 사용자 데이터
        
    Returns:
        str: 생성된 JWT 액세스 토큰
    """
    to_encode = data.copy()
    
    # 만료 시간 설정
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # JWT 토큰 생성
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """
    JWT 리프레시 토큰 생성
    
    Args:
        data (dict): 토큰에 인코딩할 사용자 데이터
        
    Returns:
        str: 생성된 JWT 리프레시 토큰
    """
    to_encode = data.copy()
    
    # 만료 시간 설정 (더 길게)
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    
    # JWT 토큰 생성 (다른 시크릿 키 사용)
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.REFRESH_TOKEN_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

async def verify_token(token: str, db):
    """
    JWT 토큰 검증 (블랙리스트 확인 포함)
    
    Args:
        token (str): 검증할 JWT 토큰
        db: MongoDB 데이터베이스 인스턴스
        
    Returns:
        dict: 토큰 페이로드
        
    Raises:
        HTTPException: 토큰이 유효하지 않거나 블랙리스트에 있는 경우
    """
    from api.auth import is_token_blacklisted
    
    # 블랙리스트 확인
    if await is_token_blacklisted(token, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그아웃된 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 기존 토큰 검증 로직
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_access_token(token: str) -> dict:
    """
    액세스 토큰 검증
    
    Args:
        token (str): 검증할 액세스 토큰
        
    Returns:
        dict: 디코드된 토큰 데이터
    """
    return verify_token(token, settings.JWT_SECRET_KEY)

def verify_refresh_token(token: str) -> dict:
    """
    리프레시 토큰 검증
    
    Args:
        token (str): 검증할 리프레시 토큰
        
    Returns:
        dict: 디코드된 토큰 데이터
    """
    return verify_token(token, settings.REFRESH_TOKEN_SECRET_KEY)

