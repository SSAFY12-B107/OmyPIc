from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr

# 사용자 기본 스키마
class UserBase(BaseModel):
    email: EmailStr
    name: str
    is_active: bool = True
    is_onboarded: bool = False
    auth_provider: str

# 사용자 생성 요청 스키마
class UserCreate(UserBase):
    password: str  # 소셜 로그인에서는 사용되지 않지만, fastapi-users에서 필요

# 사용자 업데이트 스키마
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[date] = None
    expected_opic_score: Optional[str] = None

# 온보딩 데이터 스키마
class OnboardingData(BaseModel):
    target_opic_score: str
    expected_opic_score: str
    current_opic_score: Optional[str] = None
    target_exam_date: Optional[str] = None

# 사용자 응답 스키마 (API에서 반환하는 사용자 정보)
class UserResponse(UserBase):
    id: str
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[date] = None
    expected_opic_score: Optional[str] = None
    
    class Config:
        from_attributes = True  # SQLAlchemy 모델에서 스키마 생성 허용

# 소셜 계정 스키마
class SocialAccountBase(BaseModel):
    provider: str
    social_id: str
    social_email: EmailStr

# 소셜 계정 생성 스키마
class SocialAccountCreate(SocialAccountBase):
    user_id: str

# 소셜 계정 응답 스키마
class SocialAccountResponse(SocialAccountBase):
    id: str
    user_id: str
    
    class Config:
        from_attributes = True  # SQLAlchemy 모델에서 스키마 생성 허용

# 토큰 응답 스키마
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"