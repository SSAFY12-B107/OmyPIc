from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

class ProblemModel(BaseModel):
    """문제 모델"""
    id: Optional[str] = Field(default=None, alias="_id")  # MongoDB의 _id를 문자열로 표현
    topic_category: str
    topic_group: Optional[str] = None
    problem_category: str
    content: str
    audio_s3_url: Optional[str] = None
    high_grade_kit: bool
    problem_group_id: Optional[str] = None # 그룹 ID
    problem_order: int = 0  # 그룹 내 순서 (0이면 독립 문제)
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "topic_category": "listening",
                "topic_group": "고난도",
                "problem_category": "short_conversation",
                "content": "What does the woman suggest about the report?",
                "audio_s3_url": "https://example-bucket.s3.amazonaws.com/audio/problem123.mp3",
                "high_grade_kit": True,
                "problem_group_id": "group1",
                "problem_order": 1
            }
        }
    }