from datetime import datetime
from typing import Dict, Optional, List, Any
from datetime import date
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("유효하지 않은 ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator, _field_schema):
        return {"type": "string"}
    

class User(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    auth_provider: str = "local"
    current_opic_score: Optional[str] = None
    target_opic_score: Optional[str] = None
    target_exam_date: Optional[date] = None
    is_onboarded: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    background_survey: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    
    @staticmethod
    def create_user_document(
        name: str,
        auth_provider: str = "local",
        current_opic_score: Optional[str] = None,
        target_opic_score: Optional[str] = None,
        target_exam_date: Optional[date] = None,
        is_onboarded: bool = False,
        profession: Optional[int] = None,
        is_student: Optional[bool] = None,
        studied_lecture: Optional[int] = None,
        living_place: Optional[int] = None,
        info: Optional[List[str]] = None
    ) -> Dict:
        now = datetime.now()
        
        background_survey = None
        if any(x is not None for x in [profession, is_student, studied_lecture, living_place, info]):
            background_survey = {
                "profession": profession,
                "is_student": is_student,
                "studied_lecture": studied_lecture,
                "living_place": living_place,
                "info": info or []
            }
        
        return {
            "name": name,
            "auth_provider": auth_provider,
            "current_opic_score": current_opic_score,
            "target_opic_score": target_opic_score,
            "target_exam_date": target_exam_date,
            "is_onboarded": is_onboarded,
            "created_at": now,
            "updated_at": now,
            "background_survey": background_survey
        }
