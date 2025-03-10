from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from fastapi.responses import RedirectResponse

from core.config import settings
from services.auth import fastapi_users
from core.security import auth_backend, refresh_backend, cookie_transport
from services.user_manager import UserManager, get_user_manager
from services.oauth import get_kakao_token, get_kakao_user_info
from schemas.user import TokenResponse

router = APIRouter(tags=["auth"], prefix="/auth")

# JWT 액세스 토큰 인증 라우터 추가
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
)

# 카카오 로그인 라우트
@router.get("/kakao/login")
async def kakao_login():
    """카카오 로그인 페이지로 리다이렉션"""
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={settings.KAKAO_CLIENT_ID}"
        f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
        f"&response_type=code"
    )
    return RedirectResponse(url=kakao_auth_url)

@router.get("/kakao/callback")
async def kakao_callback(
    response: Response,
    code: str, 
    user_manager: UserManager = Depends(get_user_manager),
    refresh_strategy = Depends(refresh_backend.get_strategy)
):
    """
    카카오 로그인 콜백 처리
    """
    # 액세스 토큰 요청
    token_info = await get_kakao_token(code)
    kakao_access_token = token_info.get("access_token")
    
    # 사용자 정보 요청
    user_info = await get_kakao_user_info(kakao_access_token)
    
    # 사용자 생성 또는 로그인 처리
    user = await user_manager.create_social_user(
        provider="kakao",
        social_id=user_info["social_id"],
        social_email=user_info["email"],
        name=user_info["name"],
    )
    
    # 1. 액세스 토큰 생성 (JWT) - 세션 스토리지에 저장될 짧은 수명의 토큰
    access_token = await auth_backend.get_strategy().write_token(user)
    
    # 2. 리프레시 토큰 생성 (Redis) - HTTP Only 쿠키에 저장될 긴 수명의 토큰
    refresh_token = await refresh_strategy.write_token(user)
    
    # 리프레시 토큰을 쿠키에 설정
    cookie_transport.set_refresh_token_cookie(response, refresh_token)
    
    # 프론트엔드로 리다이렉트
    # 사용자가 아직 온보딩(초기 설문)을 완료하지 않았다면 온보딩 페이지로 리다이렉트
    redirect_path = "/onboarding" if not user.is_onboarded else "/login/success"
    redirect_url = f"{settings.FRONTEND_URL}{redirect_path}?access_token={access_token}&user_id={str(user.id)}"
    
    return RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_303_SEE_OTHER
    )

# 토큰 재발급 엔드포인트
@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    response: Response,
    refresh_token: str = Cookie(None, alias="refresh_token"),
    refresh_strategy = Depends(refresh_backend.get_strategy),
    jwt_strategy = Depends(auth_backend.get_strategy),
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    리프레시 토큰을 사용하여 새 액세스 토큰과 리프레시 토큰 발급
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )
    
    try:
        # 리프레시 토큰 검증 및 사용자 가져오기
        user_id = await refresh_strategy.read_token(refresh_token)
        user = await user_manager.get(user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token or inactive user",
            )
        
        # 기존 리프레시 토큰 무효화 (보안 강화)
        await refresh_strategy.revoke_token(refresh_token)
        
        # 새 액세스 토큰 생성
        access_token = await jwt_strategy.write_token(user)
        
        # 새 리프레시 토큰 생성
        new_refresh_token = await refresh_strategy.write_token(user)
        
        # 새 리프레시 토큰을 쿠키에 설정
        cookie_transport.set_refresh_token_cookie(response, new_refresh_token)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )
    except Exception as e:
        # 토큰 검증 실패 또는 다른 오류
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

# 로그아웃 엔드포인트
@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str = Cookie(None, alias="refresh_token"),
    refresh_strategy = Depends(refresh_backend.get_strategy),
):
    """
    사용자 로그아웃 처리
    - 리프레시 토큰 쿠키 삭제
    - 리프레시 토큰 무효화 (Redis에서 제거)
    """
    # 리프레시 토큰이 있으면 Redis에서 무효화
    if refresh_token:
        try:
            await refresh_strategy.revoke_token(refresh_token)
        except Exception:
            # 토큰이 이미 만료되었거나 유효하지 않은 경우도 계속 진행
            pass
    
    # 쿠키 삭제
    response.delete_cookie(
        key="refresh_token",
        path=cookie_transport.cookie_path,
        domain=cookie_transport.cookie_domain,
        secure=cookie_transport.cookie_secure,
        httponly=cookie_transport.cookie_httponly,
    )
    
    return {"detail": "Successfully logged out"}