from fastapi import APIRouter, Request, Depends, HTTPException, status, Cookie, Response, Body
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional, Dict, Any
import httpx
import json
from urllib.parse import urlencode
from datetime import datetime, timedelta
import secrets
import jwt  # PyJWT 라이브러리 사용

from core.config import settings
from services.auth import (
    create_csrf_token, 
    verify_csrf_token, 
    create_access_token,
    create_refresh_token
)
# MongoDB 의존성 추가
from db.mongodb import get_mongodb

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
async def google_callback(
    request: Request, 
    code: str, 
    state: Optional[str] = None,
    db = Depends(get_mongodb)
):
    """
    구글 OAuth 콜백 처리 엔드포인트
    
    구글 인증 서버가 인증 코드와 state 파라미터를 포함하여 리다이렉트한 요청을 처리합니다.
    임시 코드를 생성하여 프론트엔드로 리다이렉트합니다.
    
    Args:
        request (Request): FastAPI 요청 객체
        code (str): 구글에서 제공한 인증 코드
        state (str, optional): CSRF 방지를 위한 state 파라미터
        db: MongoDB 데이터베이스 인스턴스
        
    Returns:
        RedirectResponse: 임시 코드를 포함하여 프론트엔드로 리다이렉트
        
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
        google_id = user_info.get("sub")  # Google의 고유 사용자 ID
        email = user_info.get("email", "")
        name = user_info.get("name", "")
        picture = user_info.get("picture", "")
        
        # 기존 사용자 확인 (Google ID로 검색)
        existing_user = await db.users.find_one({
            "auth_provider": "google",
            "provider_id": google_id
        })
        
        current_time = datetime.now()
        
        if existing_user:
            # 기존 사용자면 로그인 시간 업데이트
            user_id = existing_user["_id"]
            await db.users.update_one(
                {"_id": user_id},
                {"$set": {
                    "updated_at": current_time
                }}
            )
            user = existing_user
        else:
            # 새 사용자 생성 - 실제 유저 모델 구조에 맞게 저장
            new_user = {
                "name": name,
                "auth_provider": "google",
                "provider_id": google_id,  # 필요한 경우 추가
                "email": email,  # 필요한 경우 추가
                "profile_image": picture,  # 필요한 경우 추가
                "current_opic_score": None,
                "target_opic_score": None,
                "target_exam_date": None,
                "is_onboarded": False,
                "created_at": current_time,
                "updated_at": current_time,
                "background_survey": {
                    "profession": 0,
                    "is_student": False,
                    "studied_lecture": 0,
                    "living_place": 0,
                    "info": []
                },
                "average_score": {
                    "comboset_score": None,
                    "roleplaying_score": None,
                    "total_score": None,
                    "unexpected_score": None
                },
                "test_limits": {             # 초기 test_limits 구조
                    "test_count": 3,         # 기본 테스트 횟수
                    "random_problem": 5      # 기본 랜덤 문제 수
                }
            }
            
            result = await db.users.insert_one(new_user)
            user_id = result.inserted_id
            # 새 사용자 정보 조회
            user = await db.users.find_one({"_id": user_id})
        
        # ObjectId를 문자열로 변환
        user_id_str = str(user["_id"])
        
        # 5. JWT 토큰 생성
        token_payload = {
            "sub": user_id_str,
            "name": user.get("name"),
            "auth_provider": "google"
        }
        
        # JWT 토큰 생성
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token({"sub": user_id_str})
        
        # 프론트엔드에 전달할 사용자 정보
        user_data = dict(user)
        user_data["_id"] = user_id_str  # ObjectId를 문자열로 변환
        
        # 6. 임시 코드 생성 (랜덤 문자열)
        temp_code = secrets.token_urlsafe(32)
        
        # 7. 임시 코드와 JWT 토큰을 MongoDB에 저장 (15분 만료)
        expiry = datetime.now() + timedelta(minutes=15)
        
        # MongoDB 인덱스 생성 (최초 한번만 필요)
        await db.temp_codes.create_index("expires_at", expireAfterSeconds=0)
        
        # MongoDB에 임시 코드와 토큰 저장
        await db.temp_codes.insert_one({
            "code": temp_code,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user_data,
            "expires_at": expiry
        })
        
        # 8. 프론트엔드로 리다이렉트 (임시 코드 전달)
        frontend_callback_url = f"{settings.FRONTEND_URL}/auth/callback?code={temp_code}"
        return RedirectResponse(url=frontend_callback_url)

@router.post("/exchange-token")
async def exchange_token(
    code: str = Body(..., embed=True),
    db = Depends(get_mongodb)
):
    """
    임시 코드를 실제 JWT 토큰으로 교환하는 엔드포인트
    
    Args:
        code (str): 임시 코드
        db: MongoDB 데이터베이스 인스턴스
        
    Returns:
        JSONResponse: JWT 토큰과 사용자 정보를 포함한 응답
        
    Raises:
        HTTPException: 유효하지 않거나 만료된 코드일 경우
    """
    # MongoDB에서 임시 코드 검색
    temp_code_doc = await db.temp_codes.find_one({
        "code": code,
        "expires_at": {"$gt": datetime.now()}
    })
    
    # 유효한 코드인지 확인
    if not temp_code_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않거나 만료된 코드입니다"
        )
    
    # 코드 사용 후 삭제 (일회용)
    await db.temp_codes.delete_one({"code": code})
    
    # 응답 생성
    response = JSONResponse(
        content={
            "access_token": temp_code_doc["access_token"],
            "token_type": "bearer",
            "user": temp_code_doc["user"]
        }
    )
    
    # 리프레시 토큰을 쿠키에 설정
    response.set_cookie(
        key="refresh_token",
        value=temp_code_doc["refresh_token"],
        httponly=settings.COOKIE_HTTPONLY, 
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # 일 -> 초 변환
    )
    
    return response

@router.post("/logout")
async def logout(
    refresh_token: Optional[str] = Cookie(None, alias="refresh_token"),
    db = Depends(get_mongodb)
):
    """
    사용자 로그아웃 처리 엔드포인트
    
    이 엔드포인트는 다음 작업을 수행합니다:
    1. 리프레시 토큰을 블랙리스트에 추가 (토큰 무효화)
    2. 클라이언트의 쿠키에서 리프레시 토큰 삭제
    
    클라이언트는 로컬 스토리지에서 액세스 토큰도 삭제해야 합니다.
    
    Args:
        refresh_token (str, optional): 쿠키에서 추출한 리프레시 토큰
        db: MongoDB 데이터베이스 인스턴스
        
    Returns:
        JSONResponse: 로그아웃 성공 메시지 및 쿠키 삭제
    """
    response = JSONResponse(content={"message": "로그아웃 성공"})
    
    # 리프레시 토큰이 있는 경우, 블랙리스트에 추가
    if refresh_token:
        # 토큰 만료 시간 계산 (JWT 디코딩 필요)
        try:
            # PyJWT로 토큰 디코딩
            payload = jwt.decode(
                refresh_token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            
            # 토큰 만료 시간 (exp 클레임)
            if "exp" in payload:
                # exp는 Unix 타임스탬프 (초 단위)
                exp_timestamp = payload["exp"]
                expires_at = datetime.fromtimestamp(exp_timestamp)
                
                # MongoDB blacklist 컬렉션에 TTL 인덱스 생성 (최초 한번만 필요)
                await db.token_blacklist.create_index("expires_at", expireAfterSeconds=0)
                
                # 블랙리스트에 토큰 추가
                await db.token_blacklist.insert_one({
                    "token": refresh_token,
                    "expires_at": expires_at,
                    "blacklisted_at": datetime.now()
                })
        except jwt.PyJWTError:
            # 토큰 디코딩 실패시도 진행 (이미 만료된 토큰일 수 있음)
            pass
    
    # 리프레시 토큰 쿠키 삭제
    response.delete_cookie(
        key="refresh_token",
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE
    )
    
    return response

# 토큰 검증 시 블랙리스트 확인 로직
async def is_token_blacklisted(token: str, db) -> bool:
    """
    토큰이 블랙리스트에 있는지 확인
    
    Args:
        token (str): 확인할 토큰
        db: MongoDB 데이터베이스 인스턴스
        
    Returns:
        bool: 블랙리스트에 있으면 True, 없으면 False
    """
    result = await db.token_blacklist.find_one({"token": token})
    return result is not None

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
