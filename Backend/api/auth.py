from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Query
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from core.config import settings
import urllib.parse  # 추가된 import
from services.oauth import google_callback, get_naver_auth_url, naver_callback
from services.auth import refresh_access_token
from typing import Dict, Any, Optional
import secrets

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 구글 로그인 관련 엔드포인트
@router.get("/google/login")
async def google_login(redirect_uri: str = Query(None)):
    """
    구글 로그인 URL 반환 (프론트엔드에서 리다이렉트 처리)
    """
    # 상태 값 생성 (CSRF 방지 + 리다이렉트 URI 포함)
    state = secrets.token_urlsafe(16)
    
    # 리다이렉트 URI가 있는 경우 상태 값에 포함
    if redirect_uri:
        state = f"{state}:{redirect_uri}"
    
    # 구글 인증 URL 생성
    auth_url = await get_google_auth_url(state)
    
    # URL만 반환 (리다이렉트하지 않음)
    return {"auth_url": auth_url}


async def get_google_auth_url(state: str) -> str:
    """
    구글 OAuth 인증 URL 생성
    """
    client_id = settings.GOOGLE_CLIENT_ID
    redirect_uri = urllib.parse.quote(settings.GOOGLE_REDIRECT_URI)
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=email%20profile"
        f"&state={state}"
        f"&access_type=offline"
    )
    
    return auth_url

@router.get("/google/callback")
async def google_auth_callback(
    code: str = Query(...), 
    state: str = Query(None),
    response: Response = None
):
    """
    구글 OAuth 콜백 처리
    """
    # 구글 인증 처리
    auth_result = await google_callback(code, response)
    
    # 상태 값에서 리다이렉트 URI 추출
    redirect_uri = None
    if state and ":" in state:
        _, redirect_uri = state.split(":", 1)
    
    # 클라이언트 리다이렉트가 필요한 경우
    if redirect_uri:
        # 토큰과 사용자 정보를 쿼리 파라미터로 전달
        return RedirectResponse(
            url=f"{redirect_uri}?access_token={auth_result['access_token']}"
        )
    
    # 기본 응답: 토큰과 사용자 정보 반환
    return auth_result

# 네이버 로그인 관련 엔드포인트
@router.get("/naver/login")
async def naver_login(redirect_uri: str = Query(None)):
    """
    네이버 로그인 URL 반환 (프론트엔드에서 리다이렉트 처리)
    """
    # 상태 값 생성 (CSRF 방지 + 리다이렉트 URI 포함)
    state = secrets.token_urlsafe(16)
    
    # 리다이렉트 URI가 있는 경우 상태 값에 포함
    if redirect_uri:
        state = f"{state}:{redirect_uri}"
    
    # 네이버 인증 URL 생성
    auth_url = await get_naver_auth_url(state)
    
    # URL만 반환 (리다이렉트하지 않음)
    return {"auth_url": auth_url}

@router.get("/naver/callback")
async def naver_auth_callback(
    code: str = Query(...), 
    state: str = Query(...),
    response: Response = None
):
    """
    네이버 OAuth 콜백 처리
    """
    # 네이버 인증 처리
    auth_result = await naver_callback(code, state, response)
    
    # 상태 값에서 리다이렉트 URI 추출
    redirect_uri = None
    if state and ":" in state:
        _, redirect_uri = state.split(":", 1)
    
    # 클라이언트 리다이렉트가 필요한 경우
    if redirect_uri:
        # 토큰과 사용자 정보를 쿼리 파라미터로 전달
        return RedirectResponse(
            url=f"{redirect_uri}?access_token={auth_result['access_token']}"
        )
    
    # 기본 응답: 토큰과 사용자 정보 반환
    return auth_result

# 리프레시 토큰으로 액세스 토큰 갱신
@router.post("/refresh")
async def refresh_token_endpoint(refresh_token: str = Cookie(None)):
    """
    리프레시 토큰으로 새 액세스 토큰 발급
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="리프레시 토큰이 없습니다"
        )
    
    # 토큰 갱신 처리
    token_result = await refresh_access_token(refresh_token)
    
    return token_result

@router.post("/logout")
async def logout(response: Response):
    """
    로그아웃 - 클라이언트의 쿠키에서 토큰 삭제
    """
    # 쿠키에서 액세스 토큰과 리프레시 토큰 삭제
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    
    # 로그아웃 성공 메시지 반환
    return {"message": "로그아웃 되었습니다"}