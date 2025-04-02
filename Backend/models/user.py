from datetime import datetime, date
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId

class User(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")  # MongoDB의 _id를 문자열로 표현
    name: str
    email: Optional[str] = None  # 이메일 필드
    auth_provider: str = "google"
    profile_image: str = None
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[date] = None
    is_onboarded: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    background_survey: dict = Field(default_factory=lambda: {
        "profession": None,
        "is_student": None,
        "studied_lecture": None,
        "living_place": None,
        "info": []
    })
    average_score: dict = Field(default_factory=lambda: {
        "total_score": None,
        "comboset_score": None,
        "roleplaying_score": None,
        "unexpected_score": None
    }),
    # 테스트 횟수 제한 필드 추가
    limits: dict = Field(default_factory=lambda: {
        "full_test_limit": 0,  # 실전 모의고사(15문제) (최대 1회)
        "categorical_test_limit": 0,  # 유형별 문제 (최대 2회)
        "random_problem": 0, # 랜덤 1문제(최대 3회)
        "script_count": 0  # 스크립트 생성 (최대 5회)
    })

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
        
    @classmethod
    def from_mongo(cls, mongo_doc):
        """
        MongoDB 문서에서 User 모델로 변환
        """
        if mongo_doc:
            # MongoDB의 _id를 문자열로 변환
            if "_id" in mongo_doc and isinstance(mongo_doc["_id"], ObjectId):
                mongo_doc["_id"] = str(mongo_doc["_id"])
                
            # test_limits 필드가 있으면 limits로 이동
            if "test_limits" in mongo_doc and "limits" not in mongo_doc:
                mongo_doc["limits"] = mongo_doc.pop("test_limits")
                
            # limits 필드가 없는 경우 기본값 추가
            if "limits" not in mongo_doc:
                mongo_doc["limits"] = {
                    "full_test_limit": 0, 
                    "categorical_test_limit": 0, 
                    "random_problem": 0,
                    "script_count": 0 
                }
            # 기존 limits에 script_count가 없는 경우 추가
            elif "script_count" not in mongo_doc["limits"]:
                mongo_doc["limits"]["script_count"] = 0
                
            return cls(**mongo_doc)
        return None