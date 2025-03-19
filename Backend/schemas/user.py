from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime, date
from bson import ObjectId
from .custom_types import PyObjectId

# 온보딩 데이터 스키마
class OnboardingData(BaseModel):
    profession: Optional[int] = None  # 0: 사업/회사, 1: 재택근무/재택사업, 2: 교사/교육자, 3: 군복무, 4: 일 경험 없음
    is_student: Optional[bool] = None
    studied_lecture: Optional[int] = None
    living_place: Optional[int] = None
    info: Optional[List[str]] = None

# 백그라운드 서베이 스키마 (기존 코드와 호환성 유지)
class BackgroundSurvey(BaseModel):
    profession: Optional[int] = None
    is_student: Optional[bool] = None
    studied_lecture: Optional[int] = None
    living_place: Optional[int] = None
    info: Optional[List[str]] = None

# 사용자 생성 스키마
class UserCreate(BaseModel):
    name: str
    auth_provider: str = "google"  # "kakao", "google" 등
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[datetime] = None  # date 대신 datetime 사용
    is_onboarded: bool = False
    background_survey: Optional[BackgroundSurvey] = None

# 사용자 업데이트 스키마
class UserUpdate(BaseModel):
    name: Optional[str] = None
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[datetime] = None  # date 대신 datetime 사용
    is_onboarded: Optional[bool] = None
    background_survey: Optional[BackgroundSurvey] = None

# 사용자 응답 스키마
class UserResponse(BaseModel):
    id: str = Field(alias="_id")  # MongoDB의 _id를 문자열로 표현
    name: str
    auth_provider: str
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[datetime] = None  # date 대신 datetime 사용
    is_onboarded: bool
    created_at: datetime
    background_survey: Optional[Dict] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

# 사용자 인증 정보 스키마 (후에 사용)
class UserAuth(BaseModel):
    email: str
    password: str

# 토큰 정보 스키마 (후에 사용)
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
