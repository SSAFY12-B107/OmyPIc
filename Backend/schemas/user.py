from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from bson import ObjectId

# Background survey 스키마
class BackgroundSurveySchema(BaseModel):
    profession: Optional[int] = None
    is_student: Optional[bool] = None
    studied_lecture: Optional[int] = None
    living_place: Optional[int] = None
    info: Optional[List[str]] = None

# Average score 스키마
class AverageScoreSchema(BaseModel):
    comboset_score: Optional[str] = None
    roleplaying_score: Optional[str] = None
    total_score: Optional[str] = None
    unexpected_score: Optional[str] = None

# Test limits 스키마
class TestLimitsSchema(BaseModel):
    test_count: Optional[int] = None
    random_problem: Optional[int] = None

# 온보딩 데이터 스키마
class OnboardingData(BaseModel):
    target_opic_score: Optional[str] = None
    current_opic_score: Optional[str] = None
    target_exam_date: Optional[date] = None
    background_survey: Optional[Dict[str, Any]] = None


# 백그라운드 서베이 스키마
class BackgroundSurvey(BaseModel):
    profession: Optional[int] = None
    is_student: Optional[bool] = None
    studied_lecture: Optional[int] = None
    living_place: Optional[int] = None
    info: Optional[List[str]] = None

class UserCreate(BaseModel):
    name: str
    email: Optional[str] = None
    auth_provider: str = "google"
    provider_id: Optional[str] = None  # 추가
    profile_image: Optional[str] = None  # 추가
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[date] = None  # datetime이 아닌 date 타입 사용
    is_onboarded: bool = False
    background_survey: Optional[BackgroundSurvey] = None



class TestInfo(BaseModel):
    """사용자의 최근 테스트 정보"""
    test_date: List[Optional[datetime]] = Field(default_factory=list)
    test_score: List[Optional[str]] = Field(default_factory=list)
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "test_date": ["2025-03-22T19:38:35.218Z"],
                "test_score": ["NM"]
            }
        }
    }



class UserResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    email: Optional[str] = None
    auth_provider: str
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[date] = None  # datetime이 아닌 date 타입 사용
    is_onboarded: bool
    created_at: datetime
    background_survey: Optional[Dict] = None

    model_config = {  # Config 대신 model_config 사용 
        "populate_by_name": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
    }
    
    @field_validator('target_exam_date', mode='before')
    @classmethod
    def validate_target_exam_date(cls, v):
        # datetime을 date로 변환
        if isinstance(v, datetime):
            return v.date()
        return v
    


class TestInfo(BaseModel):
    """사용자의 최근 테스트 정보"""
    test_date: List[Optional[datetime]] = Field(default_factory=list)
    test_score: List[Optional[str]] = Field(default_factory=list)
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "test_date": ["2025-03-22T19:38:35.218Z"],
                "test_score": ["NM"]
            }
        }
    }

# 사용자 상세 응답 스키마 - 추가 정보 포함
class UserDetailResponse(UserResponse):
    id: str = Field(alias="_id")
    name: str
    email: Optional[str] = None
    profile_image: Optional[str] = None
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[datetime] = None
    is_onboarded: bool
    background_survey: Optional[Dict] = None
    test: Optional[TestInfo] = None

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "id": "67da4792ad60cfdcd742b119",
                "name": "이재욱",
                "email": "user@example.com",
                "profile_image": "https://example.com/profile.jpg",
                "current_opic_score": "IH",
                "target_opic_score": "AL",
                "target_exam_date": "2025-03-19",
                "is_onboarded": False,
                "background_survey": {
                    "profession": 0,
                    "is_student": False,
                    "studied_lecture": 0,
                    "living_place": 0,
                    "info": ["주거", "공원 가기", "친구/가족", "해외여행", "기술"]
                },
                "test": {
                    "test_date": ["2025-03-22T19:38:35.218Z"],
                    "test_score": ["NM"]
                }
            }
        }
    }

# 기존의 UserUpdate 클래스
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[date] = None
    is_onboarded: Optional[bool] = None
    background_survey: Optional[Dict[str, Any]] = None

# 새로운 사용자 정보 업데이트 스키마
class UserUpdateSchema(BaseModel):
    target_opic_score: Optional[str] = None
    current_opic_score: Optional[str] = None
    target_exam_date: Optional[date] = None
    is_onboarded: Optional[bool] = None
    background_survey: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_opic_score": "AL",
                "current_opic_score": "IH",
                "target_exam_date": "2025-03-19",
                "is_onboarded": False,
                "background_survey": {
                    "profession": 0,
                    "is_student": False,
                    "studied_lecture": 0,
                    "living_place": 0,
                    "info": ["주거", "공원 가기", "친구/가족", "해외여행", "기술"]
                }
            }
        }
