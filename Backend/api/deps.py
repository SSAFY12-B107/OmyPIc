# Backend/api/deps.py
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any, Optional
from services.auth import get_current_user, get_current_user_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_optional_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[Dict[str, Any]]:
    """
    현재 인증된 사용자 정보 가져오기 (선택적)
    """
    if not token:
        return None
        
    try:
        return await get_current_user(token)
    except HTTPException:
        return None

async def get_required_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    현재 인증된 사용자 정보 가져오기 (필수)
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return await get_current_user(token)

async def get_current_user_id_from_token(token: str = Depends(oauth2_scheme)) -> str:
    """
    현재 인증된 사용자 ID 가져오기
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return await get_current_user_id(token)