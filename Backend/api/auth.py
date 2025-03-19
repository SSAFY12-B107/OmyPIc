from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Dict, Any, Optional
from core.config import settings
from services import oauth as oauth_service
from services import auth as auth_service
from schemas.user import Token, UserResponse

router = APIRouter()

@router.get("/google/login")
async def google_login():
    """
    구글 OAuth 로그인 시작 엔드포인트
    """
    redirect_url = await oauth_service.get_google_auth_url()
    return {"auth_url": redirect_url}

@router.get("/google/callback")
async def google_callback(code: str, state: Optional[str] = None):
    """
    구글 OAuth 콜백 처리 엔드포인트
    """
    # 구글 OAuth 콜백 처리
    result = await oauth_service.google_callback(code)
    
    # 응답 반환
    return result

@router.get("/naver/login")
async def naver_login():
    """
    네이버 OAuth 로그인 시작 엔드포인트
    """
    # 상태 토큰 생성 (CSRF 방지용)
    state = "random_state"  # 실제로는 랜덤 문자열을 생성해야 함
    redirect_url = await oauth_service.get_naver_auth_url(state)
    return {"auth_url": redirect_url, "state": state}

@router.get("/naver/callback")
async def naver_callback(code: str, state: str):
    """
    네이버 OAuth 콜백 처리 엔드포인트
    """
    # 네이버 OAuth 콜백 처리
    result = await oauth_service.naver_callback(code, state)
    
    # 응답 반환
    return result

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """
    리프레시 토큰을 사용하여 새 액세스 토큰 발급
    """
    tokens = await auth_service.refresh_access_token(refresh_token)
    return tokens

@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(auth_service.get_current_user)):
    """
    현재 인증된 사용자 정보 조회
    """
    return token

@router.post("/logout")
async def logout(refresh_token: str):
    """
    로그아웃 처리 (리프레시 토큰 무효화)
    """
    # MongoDB에서 해당 리프레시 토큰 삭제
    db = await get_mongodb()
    tokens_collection = db.refresh_tokens
    
    result = await tokens_collection.delete_one({"token": refresh_token})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 토큰"
        )
    
    return {"message": "로그아웃 성공"}