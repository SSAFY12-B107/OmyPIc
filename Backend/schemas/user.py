from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Annotated
from datetime import datetime, date
from bson import ObjectId
from .custom_types import PyObjectId

# 온보딩 데이터 스키마
class OnboardingData(BaseModel):
    profession: Optional[int] = None  # 0: 사업/회사, 1: 재택근무/재택사업, 2: 교사/교육자, 3: 군복무, 4: 일 경험 없음
    is_student: Optional[bool] = None  # True 또는 False
    studied_lecture: Optional[int] = None  # 0: 학위 과정 수업, 1: 전문 기술 향상을 위한 평생 학습, 2: 어학 수업, 3: 수강 후 5년 이상 지남
    living_place: Optional[int] = None  # 0: 개인 주택이나 아파트에 홀로 거주, 1: 친구나 룸메이트와 주택이나 아파트에 거주, 2: 가족과 함께 주택이나 아파트에 거주, 3: 학교 기숙사, 4: 군대 막사
    info: Optional[List[str]] = None  # 추가 정보(여가/취미/운동/여행) - 문자열 리스트

# 백그라운드 서베이 스키마 (기존 코드와 호환성 유지)
class BackgroundSurvey(BaseModel):
    profession: Optional[int] = None  # 0: 사업/회사, 1: 재택근무/재택사업, 2: 교사/교육자, 3: 군복무, 4: 일 경험 없음
    is_student: Optional[bool] = None  # True 또는 False
    studied_lecture: Optional[int] = None  # 0: 학위 과정 수업, 1: 전문 기술 향상을 위한 평생 학습, 2: 어학 수업, 3: 수강 후 5년 이상 지남
    living_place: Optional[int] = None  # 0: 개인 주택이나 아파트에 홀로 거주, 1: 친구나 룸메이트와 주택이나 아파트에 거주, 2: 가족과 함께 주택이나 아파트에 거주, 3: 학교 기숙사, 4: 군대 막사
    info: Optional[List[str]] = None  # 추가 정보(여가/취미/운동/여행) - 문자열 리스트

# 사용자 생성 스키마
class UserCreate(BaseModel):
    name: str
    auth_provider: str = "local"  # "local", "kakao", "google" 등
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[date] = None
    is_onboarded: bool = False
    background_survey: Optional[BackgroundSurvey] = None

# 사용자 업데이트 스키마
class UserUpdate(BaseModel):
    name: Optional[str] = None
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[date] = None
    is_onboarded: Optional[bool] = None
    background_survey: Optional[BackgroundSurvey] = None

# 사용자 응답 스키마
class UserResponse(BaseModel):
    id: Annotated[PyObjectId, Field(alias="_id")]
    user_id: int
    name: str
    auth_provider: str
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[date] = None
    is_onboarded: bool
    created_at: datetime
    background_survey: Optional[BackgroundSurvey] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
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