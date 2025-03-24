from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date

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

# 사용자 생성 스키마
class UserCreate(BaseModel):
    name: str
    email: Optional[str] = None
    auth_provider: str = "google"
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[date] = None
    background_survey: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "홍길동",
                "email": "user@example.com",
                "auth_provider": "google",
                "current_opic_score": "IH",
                "target_opic_score": "AL",
                "target_exam_date": "2025-03-19"
            }
        }

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



# 사용자 응답 스키마 - 기본 정보
class UserResponse(BaseModel):
    id: str
    name: str
    auth_provider: str
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[date] = None
    is_onboarded: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    background_survey: Optional[Dict[str, Any]] = None
    average_score: Optional[Dict[str, Any]] = None
    test_limits: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "67da4792ad60cfdcd742b119",
                "name": "이재욱",
                "auth_provider": "google",
                "current_opic_score": "IH",
                "target_opic_score": "AL",
                "target_exam_date": "2025-03-19",
                "is_onboarded": False,
                "created_at": "2025-03-19T13:26:58.049Z",
                "updated_at": "2025-03-23T16:55:20.952Z",
                "background_survey": {
                    "profession": 0,
                    "is_student": False,
                    "studied_lecture": 0,
                    "living_place": 0,
                    "info": ["주거", "공원 가기", "친구/가족", "해외여행", "기술"]
                },
                "average_score": {
                    "comboset_score": "IH",
                    "roleplaying_score": "AL",
                    "total_score": "IH",
                    "unexpected_score": "IM3"
                },
                "test_limits": {
                    "test_count": 3,
                    "random_problem": 5
                }
            }
        }

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
