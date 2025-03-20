# Backend/services/auth.py
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import jwt
from fastapi import HTTPException, status
from core.config import settings
from db.mongodb import get_mongodb
from bson import ObjectId

async def create_tokens(data: Dict[str, Any]) -> Dict[str, str]:
    """
    액세스 토큰과 리프레시 토큰 생성
    """
    # 사용자 ID를 문자열로 변환
    if "user_id" in data and isinstance(data["user_id"], ObjectId):
        data["user_id"] = str(data["user_id"])
    
    # 액세스 토큰 생성
    access_token_expires = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token_data = {
        **data,
        "exp": access_token_expires.timestamp()
    }
    access_token = jwt.encode(
        access_token_data, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    # 리프레시 토큰 생성
    refresh_token_expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token_data = {
        **data,
        "exp": refresh_token_expires.timestamp()
    }
    refresh_token = jwt.encode(
        refresh_token_data, 
        settings.REFRESH_TOKEN_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    # MongoDB에 리프레시 토큰 저장
    await store_refresh_token(refresh_token, data.get("user_id"), refresh_token_expires)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

async def store_refresh_token(refresh_token: str, user_id: str, expires_at: datetime) -> None:
    """
    리프레시 토큰을 데이터베이스에 저장
    """
    db = await get_mongodb()
    tokens_collection = db.refresh_tokens
    
    # 기존 토큰이 있다면 삭제
    await tokens_collection.delete_many({"user_id": user_id})
    
    # 새 토큰 저장
    token_doc = {
        "token": refresh_token,
        "user_id": user_id,
        "expires_at": expires_at,
        "created_at": datetime.utcnow()
    }
    
    await tokens_collection.insert_one(token_doc)

async def refresh_access_token(refresh_token: str) -> Dict[str, str]:
    """
    리프레시 토큰을 사용하여 새 액세스 토큰 발급
    """
    try:
        # 리프레시 토큰 검증
        payload = jwt.decode(
            refresh_token, 
            settings.REFRESH_TOKEN_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 데이터베이스에서 토큰 확인
        db = await get_mongodb()
        tokens_collection = db.refresh_tokens
        stored_token = await tokens_collection.find_one({
            "token": refresh_token,
            "user_id": user_id
        })
        
        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="리프레시 토큰이 유효하지 않습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 새 액세스 토큰 생성
        access_token_data = {"user_id": user_id}
        tokens = await create_tokens(access_token_data)
        
        return tokens
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었거나 유효하지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str) -> Dict[str, Any]:
    """
    JWT 토큰으로부터 현재 인증된 사용자 정보 가져오기
    """
    from services.user import get_user_by_id  # 순환 참조 방지를 위한 지연 임포트
    
    try:
        # 토큰 검증
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 사용자 정보 조회
        user = await get_user_by_id(ObjectId(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다",
            )
        
        return user
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었거나 유효하지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )