from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime


# 테스트 히스토리 응답 모델

class TestScoreInfo(BaseModel):
    """테스트 점수 요약 정보"""
    total_score: Optional[str] = None
    comboset_score: Optional[str] = None
    roleplaying_score: Optional[str] = None
    unexpected_score: Optional[str] = None

class TestHistoryItem(BaseModel):
    """테스트 히스토리 항목"""
    id: str
    test_date: datetime
    test_type: bool
    test_score: Optional[TestScoreInfo] = None

class TestHistoryResponse(BaseModel):
    """테스트 히스토리 응답 모델"""
    average_score: Optional[str] = None
    test_history: List[TestHistoryItem] = []


# 테스트 상세세 응답 모델

class ProblemDetailResponseFeedback(BaseModel):
    """문제별 피드백 상세 정보 응답 모델"""
    paragraph: Optional[str] = None
    vocabulary: Optional[str] = None
    spoken_amount: Optional[str] = None

class ProblemDetailResponse(BaseModel):
    """문제 상세 정보 응답 모델"""
    problem: Optional[str] = None
    user_response: Optional[str] = None
    score: Optional[str] = None
    feedback: Optional[ProblemDetailResponseFeedback] = None

class ScoreDetailResponse(BaseModel):
    """점수 상세 정보 응답 모델"""
    total_score: Optional[str] = None
    comboset_score: Optional[str] = None
    roleplaying_score: Optional[str] = None
    unexpected_score: Optional[str] = None

class FeedbackDetailResponse(BaseModel):
    """피드백 상세 정보 응답 모델"""
    total_feedback: Optional[str] = None
    paragraph: Optional[str] = None
    vocabulary: Optional[str] = None
    spoken_amount: Optional[str] = None

class TestDetailResponse(BaseModel):
    """테스트 상세 응답 모델"""
    id: str = Field(..., alias="_id")
    test_type: bool
    test_score: Optional[ScoreDetailResponse] = None
    test_feedback: Optional[FeedbackDetailResponse] = None
    problem_data: Dict[str, ProblemDetailResponse] = {}
    test_date: datetime
    user_id: Optional[str] = None
    
    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }