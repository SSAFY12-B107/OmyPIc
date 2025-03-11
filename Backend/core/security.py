from fastapi import Depends, Response
from fastapi_users.authentication import (
    AuthenticationBackend, 
    BearerTransport, 
    CookieTransport,
    JWTStrategy,
)

from core.config import settings

# 액세스 토큰용 Bearer 전송 방식 (Authorization 헤더 사용)
bearer_transport = BearerTransport(tokenUrl="/api/auth/jwt/login")

# CustomCookieTransport 클래스 정의
class CustomCookieTransport(CookieTransport):
    """
    기본 CookieTransport를 확장하여 쿠키를 직접 설정할 수 있는 메서드 추가
    """
    def set_refresh_token_cookie(self, response: Response, token: str):
        """
        응답 객체에 리프레시 토큰 쿠키를 직접 설정
        """
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            max_age=self.cookie_max_age,
            path=self.cookie_path,
            domain=self.cookie_domain,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite,
        )

# 리프레시 토큰용 커스텀 쿠키 전송 방식
cookie_transport = CustomCookieTransport(
    cookie_name="refresh_token",
    cookie_max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 일 -> 초 변환
    cookie_secure=settings.COOKIE_SECURE,
    cookie_httponly=settings.COOKIE_HTTPONLY,
    cookie_samesite=settings.COOKIE_SAMESITE,
)

# 액세스 토큰 생성 전략 (JWT)
# 짧은 만료 시간 (15분)
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.SECRET_KEY, 
        lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        algorithm=settings.JWT_ALGORITHM,
        token_audience=["fastapi-users:auth"]
    )

# 리프레시 토큰 생성 전략 (JWT)
# 긴 만료 시간 (7일)
def get_refresh_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.REFRESH_TOKEN_SECRET_KEY,  # 리프레시 토큰용 별도 시크릿 키 사용
        lifetime_seconds=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        algorithm=settings.JWT_ALGORITHM,
        token_audience=["fastapi-users:refresh"]
    )

# 액세스 토큰용 인증 백엔드
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# 리프레시 토큰용 인증 백엔드
refresh_backend = AuthenticationBackend(
    name="refresh",
    transport=cookie_transport,
    get_strategy=get_refresh_strategy,
)