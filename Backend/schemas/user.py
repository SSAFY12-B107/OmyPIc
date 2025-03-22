# Backend/schemas/user.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from bson import ObjectId
from .custom_types import PyObjectId

# 온보딩 데이터 스키마
class OnboardingData(BaseModel):
    profession: Optional[int] = None
    is_student: Optional[bool] = None
    studied_lecture: Optional[int] = None
    living_place: Optional[int] = None
    info: Optional[List[str]] = None

# 백그라운드 서베이 스키마
class BackgroundSurvey(BaseModel):
    profession: Optional[int] = None
    is_student: Optional[bool] = None
    studied_lecture: Optional[int] = None
    living_place: Optional[int] = None
    info: Optional[List[str]] = None

# 사용자 생성 스키마
class UserCreate(BaseModel):
    name: str
    email: Optional[str] = None  # 이메일 필드 추가
    auth_provider: str = "google"
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[datetime] = None
    is_onboarded: bool = False
    background_survey: Optional[BackgroundSurvey] = None

# 사용자 업데이트 스키마
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None  # 이메일 필드 추가
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[datetime] = None
    is_onboarded: Optional[bool] = None
    background_survey: Optional[BackgroundSurvey] = None

# 사용자 응답 스키마
class UserResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    email: Optional[str] = None  # 이메일 필드 추가
    auth_provider: str
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[datetime] = None
    is_onboarded: bool
    created_at: datetime
    background_survey: Optional[Dict] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }


class TestInfo(BaseModel):
    test_date: List[Optional[datetime]] = None
    test_score:List[Optional[str]] = None


# 사용자 프로필 정보 응답 스키마
class UserDetailResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    email: Optional[str]
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[datetime] = None
    is_onboarded: bool
    background_survey: Optional[Dict] = None
    test: Optional[TestInfo] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

# 사용자 인증 정보 스키마
class UserAuth(BaseModel):
    email: str
    password: str

# 토큰 정보 스키마
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None