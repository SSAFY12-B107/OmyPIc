from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class QuestionCreate(BaseModel):
    """질문 생성 모델"""
    content: str  # 질문 내용
    problem_category: str  # problem의 problem_category와 동일


class QuestionResponse(BaseModel):
    """질문 응답 모델"""
    id: str = Field(alias="_id")  # MongoDB의 _id를 문자열로 표현
    content: str  # 질문 내용
    problem_category: str  # problem의 problem_category와 동일
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "content": "지금 머릿속에 가장 먼저 떠오르는 이미지는 어떤 것인가요?",
                "problem_category": "묘사",
            }
        }
    }