import os
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "OmyPIC"
    PROJECT_DESCRIPTION: str = "단기 오픽 성적 취득 서비스"
    PROJECT_VERSION: str = "0.1.0"
    
    # SECURITY
    SECRET_KEY: str = os.getenv("SECRET_KEY")  # 액세스 토큰용 시크릿 키
    REFRESH_TOKEN_SECRET_KEY: str = os.getenv("REFRESH_TOKEN_SECRET_KEY")  # 리프레시 토큰용 시크릿 키
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 액세스 토큰 만료 시간(분) - 짧게 설정
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # 리프레시 토큰 만료 시간(일)
    
    # COOKIE SETTINGS
    COOKIE_SECURE: bool = False  # 프로덕션 환경에서는 True로 설정
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "lax"  # 프로덕션 환경에서는 "strict"로 고려
    
    # DATABASE
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # CORS
    CORS_ORIGINS: List[str] = []
    
    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []
    
    # 카카오 OAuth 설정
    KAKAO_CLIENT_ID: str = os.getenv("KAKAO_CLIENT_ID", "YOUR_KAKAO_CLIENT_ID")
    KAKAO_CLIENT_SECRET: str = os.getenv("KAKAO_CLIENT_SECRET", "YOUR_KAKAO_CLIENT_SECRET")
    KAKAO_REDIRECT_URI: str = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8000/api/auth/kakao/callback")
    
    # Google OAuth 설정 (추후 구현을 위한 설정)
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
    
    # 프론트엔드 URL
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # extra 환경변수를 무시하도록 설정

# 설정 인스턴스 생성
settings = Settings()