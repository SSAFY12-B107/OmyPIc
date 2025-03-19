# Backend/models/user.py
from datetime import datetime, date
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId

class User(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")  # MongoDB의 _id를 문자열로 표현
    name: str
    email: Optional[str] = None  # 이메일 필드 추가
    auth_provider: str = "google"
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

    class Config:
        allow_population_by_field_name = True
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
            return cls(**mongo_doc)
        return None