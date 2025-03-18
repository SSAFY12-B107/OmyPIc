from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ProblemDetail(BaseModel):
    """문제 상세 정보 모델"""
    problem: Optional[str] = None  # 문제 내용 
    user_response: Optional[str] = None  # 사용자 응답
    feedback: Optional[str] = None  # 피드백
    score: Optional[str] = None  # 점수


class TestModel(BaseModel):
    """테스트(모의고사) 모델"""
    id: Optional[str] = Field(default=None, alias="_id")  # MongoDB의 _id를 문자열로 표현
    test_type: bool  # 테스트 유형 (False: Full, True: Half(속성))
    test_score: Optional[str] = None  # 테스트 총합 점수
    problem_data: Dict[int, ProblemDetail] = Field(default_factory=dict)  # 문제 번호를 키로 하는 문제 상세 정보
    test_date: datetime = Field(default_factory=datetime.now)  # 테스트 날짜
    user_id: Optional[str] = None  # 사용자 ID(MongoDB ObjectId를 문자열로 표현)
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "test_type": False,
                "test_score": "85",
                "user_id": "507f1f77bcf86cd799439022",
                "test_date": "2023-10-15T09:30:00"
            }
        }
    }

