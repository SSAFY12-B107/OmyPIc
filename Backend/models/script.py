from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ScriptModel(BaseModel):
    """테스트(모의고사) 모델"""
    id: Optional[str] = Field(default=None, alias="_id")  # MongoDB의 _id를 문자열로 표현
    user_id: str = Field(...)  # 사용자 ID(MongoDB ObjectId를 문자열로 표현)  # 테스트 유형 (False: Full, True: Half(속성))
    problem_id: str = Field(...)
    content: str
    created_at: datetime= Field(default_factory=datetime.now)  # 테스트 날짜
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

