import os
from typing import List, Optional, Any
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "OmyPIC"
    PROJECT_DESCRIPTION: str = "단기 오픽 성적 취득 서비스"
    PROJECT_VERSION: str = "0.1.0"
    
    # 환경 설정
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    IS_DEVELOPMENT: bool = ENVIRONMENT == "development"
    
    # SECURITY
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "default_secret_key_for_dev")  # 액세스 토큰용 시크릿 키
    REFRESH_TOKEN_SECRET_KEY: str = os.getenv("REFRESH_TOKEN_SECRET_KEY", "default_refresh_key_for_dev")  # 리프레시 토큰용 시크릿 키
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 액세스 토큰 만료 시간(분) - 짧게 설정
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # 리프레시 토큰 만료 시간(일)
    
    # COOKIE SETTINGS
    COOKIE_SECURE: bool = not IS_DEVELOPMENT  # 개발환경에서는 False, 운영환경에서는 True
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "lax"  # 프로덕션 환경에서는 "strict"로 고려
    COOKIE_DOMAIN_DEV: str = os.getenv("COOKIE_DOMAIN_DEV", "localhost")
    COOKIE_DOMAIN_PROD: str = os.getenv("COOKIE_DOMAIN_PROD", "omypic.store")
    
    # DATABASE
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "omypic_db")
    
    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # OAuth 설정
    NAVER_CLIENT_ID: str = os.getenv("NAVER_CLIENT_ID", "NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET: str = os.getenv("NAVER_CLIENT_SECRET", "NAVER_CLIENT_SECRET")
    NAVER_REDIRECT_URI: str = os.getenv("NAVER_REDIRECT_URI", "http://localhost:8000/api/auth/naver/callback")
    
    # Google OAuth 설정 (추후 구현을 위한 설정)
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
    
    # AWS S3 설정
    AWS_ACCESS_KEY_ID: str = Field(..., env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(..., env="AWS_REGION")
    AWS_S3_BUCKET_NAME: str = Field(..., env="AWS_S3_BUCKET_NAME")

    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    GEMINI_API_KEYS: str = os.getenv("GEMINI_API_KEYS")
    GROQ_API_KEYS: str = os.getenv("GROQ_API_KEYS")
    
    def cors_origins(self) -> List[str]:
        return [i.strip() for i in self.CORS_ORIGINS.split(",") if i.strip()]
    
    def gemini_api_keys(self) -> List[str]:
        return [i.strip() for i in self.GEMINI_API_KEYS.split(",") if i.strip()]
    
    def groq_api_keys(self) -> List[str]:
        return [i.strip() for i in self.GROQ_API_KEYS.split(",") if i.strip()]

    @property
    def cookie_domain(self) -> str:
        """현재 환경에 맞는 쿠키 도메인을 반환합니다."""
        return self.COOKIE_DOMAIN_DEV if self.IS_DEVELOPMENT else self.COOKIE_DOMAIN_PROD
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # extra 환경변수를 무시하도록 설정

# 설정 인스턴스 생성
settings = Settings()