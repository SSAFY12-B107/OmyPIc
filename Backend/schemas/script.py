from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ScriptCreate(BaseModel):
    """스크립트 생성 모델"""
    user_id: str
    problem_id: str
    content: str
    is_script: bool = False


class ScriptResponse(BaseModel):
    """스크립트 응답 모델"""
    id: str = Field(alias="_id")
    user_id: str
    problem_id: str
    content: str
    created_at: datetime
    is_script: bool
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "user_id": "507f1f77bcf86cd799439011",
                "problem_id": "507f1f77bcf86cd799439011",
                "content": "Hello, I'm Yunha Kim.",
                "created_at": "2023-10-15T09:30:00",
                "is_script": False
            }
        }
    }