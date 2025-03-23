from fastapi import APIRouter, Request, Depends, HTTPException, status, Cookie, Response
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional, Dict, Any
import httpx
import json
from urllib.parse import urlencode

from core.config import settings
from services.auth import (
    create_csrf_token, 
    verify_csrf_token, 
    create_access_token,
    create_refresh_token
)

router = APIRouter()
@router.get("/google/login")
async def login_google():
    """
    구글 OAuth 로그인 초기화 엔드포인트
    
    이 엔드포인트는 클라이언트를 구글 로그인 페이지로 리다이렉트합니다.
    CSRF 공격 방지를 위해 서명된 state 파라미터를 생성하고 사용합니다.
    
    Returns:
        RedirectResponse: 구글 OAuth 인증 페이지로의 리다이렉트
    """
    # CSRF 방지를 위한 서명된 state 파라미터 생성
    state = create_csrf_token()
    
    # 구글 OAuth 인증 URL 생성
    auth_url = "https://accounts.google.com/o/oauth2/auth"
    
    # 요청 파라미터 구성
    params = {
        # Google API Console에서 발급받은 클라이언트 ID
        "client_id": settings.GOOGLE_CLIENT_ID,

        # 사용자가 인증을 마친 후 리디렉션될 URI
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,

        # 응답 방식: 'code'를 사용하면 Authorization Code Flow를 의미
        "response_type": "code",

        # 요청할 사용자 정보 범위: 이메일, 프로필 기본 정보
        "scope": "email profile",

        # CSRF 방지를 위한 고유한 상태값 (서명된 토큰 등 사용)
        "state": state,

        # 오프라인 접근 허용: refresh_token을 발급받기 위해 사용
        "access_type": "offline",

        # 항상 사용자에게 동의 화면을 보여줌
        # 기본적으로는 이전에 승인한 사용자는 동의 화면이 생략됨
        # 하지만 prompt=consent를 사용하면 매번 동의 화면을 강제로 보여줌
        # → 그 결과 항상 refresh_token을 받을 수 있음
        "prompt": "consent"
    }
    
    # 쿼리 파라미터를 URL에 추가
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    authorization_url = f"{auth_url}?{query_string}"
    
    # 구글 로그인 페이지로 리다이렉트
    return RedirectResponse(authorization_url)

@router.get("/google/callback")
async def google_callback(request: Request, code: str, state: Optional[str] = None):
    """
    구글 OAuth 콜백 처리 엔드포인트
    
    구글 인증 서버가 인증 코드와 state 파라미터를 포함하여 리다이렉트한 요청을 처리합니다.
    
    Args:
        request (Request): FastAPI 요청 객체
        code (str): 구글에서 제공한 인증 코드
        state (str, optional): CSRF 방지를 위한 state 파라미터
        
    Returns:
        JSONResponse: 인증 성공 시 토큰과 사용자 정보 반환
        
    Raises:
        HTTPException: 인증 실패 시 오류 발생
    """
    # 1. state 파라미터 검증 (CSRF 방지)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="State 파라미터가 누락되었습니다"
        )
    
    try:
        verify_csrf_token(state)
    except HTTPException as e:
        # CSRF 토큰 검증 실패
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 state 파라미터입니다"
        )
    
    # 2. 인증 코드를 사용하여 액세스 토큰 요청
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        # 토큰 요청
        token_response = await client.post(token_url, data=token_data)
        
        # 응답 확인
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"구글 토큰 요청 실패: {token_response.text}"
            )
        
        # 토큰 데이터 파싱
        token_info = token_response.json()
        access_token = token_info.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="액세스 토큰을 받지 못했습니다"
            )
        
        # 3. 액세스 토큰으로 사용자 정보 요청
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        userinfo_response = await client.get(userinfo_url, headers=headers)
        
        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"사용자 정보 요청 실패: {userinfo_response.text}"
            )
        
        # 사용자 정보 파싱
        user_info = userinfo_response.json()
        
        # 4. 사용자 정보 검증 및 DB 처리
        # (실제 구현에서는 여기서 DB에 사용자 정보를 저장하거나 업데이트)
        user_data = {
            "id": user_info.get("sub"),  # Google의 고유 사용자 ID
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "provider": "google"
        }
        
        # 5. JWT 토큰 생성
        # 액세스 토큰용 페이로드
        token_payload = {
            "sub": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "provider": "google"
        }
        
        # JWT 토큰 생성
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token({"sub": user_data["id"]})
        
        # 6. 응답 생성
        response = JSONResponse(
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_data
            }
        )
        
        # 리프레시 토큰을 쿠키에 설정
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=settings.COOKIE_HTTPONLY,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # 일 -> 초 변환
        )
        
        return response

# 유틸리티 함수 추가
def create_query_string(params: Dict[str, Any]) -> str:
    """
    파라미터 딕셔너리를 URL 쿼리 문자열로 변환
    
    Args:
        params (Dict[str, Any]): 파라미터 딕셔너리
        
    Returns:
        str: URL 인코딩된 쿼리 문자열
    """
    return urlencode(params)
