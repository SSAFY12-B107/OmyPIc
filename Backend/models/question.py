from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class QuestionModel(BaseModel):
    """스크립트 질문 모델"""
    id: Optional[str] = Field(default=None, alias="_id")  # MongoDB의 _id를 문자열로 표현
    content: str  # 질문 내용
    problem_category: str  # problem의 problem_category와 동일
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "content": "지금 머릿속에 가장 먼저 떠오르는 이미지는 어떤 것인가요? 그 장면을 조금만 더 자세히 묘사해 주시겠어요?",
                "problem_category": "묘사",
            }
        }
    }

