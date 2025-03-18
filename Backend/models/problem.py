from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class ProblemModel(BaseModel):
    """문제 모델"""
    id: Optional[str] = Field(default=None, alias="_id")  # MongoDB의 _id를 문자열로 표현
    topic_category: str
    problem_category: str
    content: str
    audio_s3_url: Optional[str] = None
    high_grade_kit: bool
    connected_problem: Optional[List[str]] = None
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "topic_category": "listening",
                "problem_category": "short_conversation",
                "content": "What does the woman suggest about the report?",
                "audio_s3_url": "https://example-bucket.s3.amazonaws.com/audio/problem123.mp3",
                "high_grade_kit": True,
                "connected_problem": ["507f1f77bcf86cd799439012", "507f1f77bcf86cd799439013"]
            }
        }
    }