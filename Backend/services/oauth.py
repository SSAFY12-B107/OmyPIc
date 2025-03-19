# Backend/services/oauth.py
import httpx
from fastapi import HTTPException, status
from typing import Dict, Any, Optional
from core.config import settings
from db.mongodb import get_mongodb
from services.user import create_user, get_user_by_email
from services.auth import create_tokens
from bson import ObjectId

# 구글 OAuth URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# 네이버 OAuth URLs
NAVER_AUTH_URL = "https://nid.naver.com/oauth2.0/authorize"
NAVER_TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
NAVER_USERINFO_URL = "https://openapi.naver.com/v1/nid/me"

async def get_google_auth_url(state: str = None) -> str:
    """
    구글 OAuth 인증 URL 생성
    """
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "email profile",
    }
    
    if state:
        params["state"] = state
        
    # URL 파라미터 구성
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    return f"{GOOGLE_AUTH_URL}?{query_string}"

async def get_naver_auth_url(state: str = None) -> str:
    """
    네이버 OAuth 인증 URL 생성
    """
    params = {
        "client_id": settings.NAVER_CLIENT_ID,
        "redirect_uri": settings.NAVER_REDIRECT_URI,
        "response_type": "code",
        "state": state or "random_state",  # 네이버는 state 파라미터가 필수
    }
    
    # URL 파라미터 구성
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    return f"{NAVER_AUTH_URL}?{query_string}"

async def google_callback(code: str) -> Dict[str, Any]:
    """
    구글 OAuth 콜백 처리 및 사용자 정보 조회
    """
    # 토큰 요청
    token_payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": code,
    }
    
    async with httpx.AsyncClient() as client:
        # 액세스 토큰 요청
        token_response = await client.post(GOOGLE_TOKEN_URL, data=token_payload)
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google OAuth 토큰 오류: {token_response.text}"
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # 사용자 정보 요청
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_response = await client.get(GOOGLE_USERINFO_URL, headers=headers)
        
        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사용자 정보를 가져오는데 실패했습니다."
            )
        
        user_data = userinfo_response.json()
        
        # 필요한 사용자 정보 추출
        email = user_data.get("email")
        name = user_data.get("name")
        picture = user_data.get("picture")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이메일 정보를 가져오는데 실패했습니다."
            )
            
        # 사용자 처리 (기존 사용자 조회 또는 새로운 사용자 생성)
        user = await process_oauth_user(email=email, name=name, auth_provider="google")
        
        # JWT 토큰 생성
        tokens = await create_tokens({"user_id": user["_id"]})
        
        return {
            "user": user,
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer"
        }

async def naver_callback(code: str, state: str) -> Dict[str, Any]:
    """
    네이버 OAuth 콜백 처리 및 사용자 정보 조회
    """
    # 토큰 요청
    token_payload = {
        "client_id": settings.NAVER_CLIENT_ID,
        "client_secret": settings.NAVER_CLIENT_SECRET,
        "redirect_uri": settings.NAVER_REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": code,
        "state": state,
    }
    
    async with httpx.AsyncClient() as client:
        # 액세스 토큰 요청
        token_response = await client.post(NAVER_TOKEN_URL, data=token_payload)
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Naver OAuth 토큰 오류: {token_response.text}"
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # 사용자 정보 요청
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_response = await client.get(NAVER_USERINFO_URL, headers=headers)
        
        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사용자 정보를 가져오는데 실패했습니다."
            )
        
        user_data = userinfo_response.json()
        
        # 네이버 API는 response 내부에 사용자 정보가 있음
        if "response" not in user_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="네이버 API 응답 형식이 올바르지 않습니다."
            )
            
        response_data = user_data["response"]
        
        # 필요한 사용자 정보 추출
        email = response_data.get("email")
        name = response_data.get("name")
        
        if not email or not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이메일 또는 이름 정보를 가져오는데 실패했습니다."
            )
            
        # 사용자 처리 (기존 사용자 조회 또는 새로운 사용자 생성)
        user = await process_oauth_user(email=email, name=name, auth_provider="naver")
        
        # JWT 토큰 생성
        tokens = await create_tokens({"user_id": user["_id"]})
        
        return {
            "user": user,
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer"
        }

async def process_oauth_user(email: str, name: str, auth_provider: str) -> Dict[str, Any]:
    """
    OAuth 사용자 처리 (기존 사용자 조회 또는 새로운 사용자 생성)
    """
    # 이메일로 기존 사용자 조회
    user = await get_user_by_email(email)
    
    if user:
        # 기존 사용자가 있는 경우
        return user
    else:
        # 신규 사용자 생성
        new_user = await create_user(
            name=name,
            email=email,
            auth_provider=auth_provider
        )
        return new_user

async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    이메일로 사용자 조회
    """
    db = await get_mongodb()
    users_collection = db.users
    
    user = await users_collection.find_one({"email": email})
    
    if user:
        user["_id"] = str(user["_id"])  # ObjectId를 문자열로 변환
    
    return user