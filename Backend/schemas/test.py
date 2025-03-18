from typing import Optional, Dict
from models.test import ProblemDetail, TestModel
from pydantic import BaseModel

class TestCreate(BaseModel):
    """테스트 생성 모델 (입력용)"""
    test_type: bool
    user_id: str  # 사용자의 ObjectId를 문자열로 받음
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "test_type": False,
                "user_id": "507f1f77bcf86cd799439022"
            }
        }
    }


class TestUpdate(BaseModel):
    """테스트 업데이트 모델"""
    test_score: Optional[str] = None
    problem_data: Optional[Dict[int, ProblemDetail]] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "test_score": "90",
                "problem_data": {
                    "1": {
                        "problem": "문제 내용",
                        "user_response": "사용자 응답",
                        "feedback": "피드백",
                        "score": "5"
                    }
                }
            }
        }
    }