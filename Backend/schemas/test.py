from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from models.test import TestTypeEnum


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
    overall_feedback_status: Optional[str] = None
    test_date: datetime
    test_type: bool
    test_type_str: Optional[TestTypeEnum] = None  # 새 필드 추가
    test_score: Optional[TestScoreInfo] = None

class TestCountInfo(BaseModel):
    """테스트 생성 횟수 정보"""
    used: int
    limit: int
    remaining: int

class TestCounts(BaseModel):
    """모든 테스트 생성 횟수 정보"""
    test_count: TestCountInfo
    categorical_test_count: TestCountInfo
    random_problem: TestCountInfo
    script_count: Optional[TestCountInfo] = None

class TestHistoryResponse(BaseModel):
    """테스트 히스토리 응답 모델"""
    average_score: Optional[TestScoreInfo] = None
    test_history: List[TestHistoryItem] = []
    test_counts: TestCounts


# 테스트 상세 응답 모델

class ProblemDetailResponseFeedback(BaseModel):
    """문제별 피드백 상세 정보 응답 모델"""
    paragraph: Optional[str] = None
    vocabulary: Optional[str] = None
    spoken_amount: Optional[str] = None

class ProblemDetailResponse(BaseModel):
    """문제 상세 정보 응답 모델"""
    problem_id: Optional[str] = None  # 문제 ID
    problem_category: Optional[str] = None  # 문제 카테고리
    topic_category: Optional[str] = None  # 문제 카테고리
    problem: Optional[str] = None
    user_response: Optional[str] = None
    score: Optional[str] = None
    feedback: Optional[ProblemDetailResponseFeedback] = None
    processing_status: Optional[str] = None
    processing_message: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None

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
    user_id: Optional[str] = None
    test_type: bool
    test_type_str: Optional[TestTypeEnum] = None  # 새 필드 추가
    test_date: datetime
    test_score: Optional[ScoreDetailResponse] = None
    test_feedback: Optional[FeedbackDetailResponse] = None
    problem_data: Dict[str, ProblemDetailResponse] = {}
    overall_feedback_status: Optional[str] = None
    overall_feedback_message: Optional[str] = None
    
    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


# 테스트 생성을 위한 요청 모델
class CreateTestRequest(BaseModel):
    """테스트 생성 요청 모델"""
    user_id: str  # 사용자 ID
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "507f1f77bcf86cd799439022"
            }
        }
    }

class TestCreationProblemDetail(BaseModel):
    """테스트 생성시 문제 상세 정보 응답 모델"""
    problem_id: Optional[str] = None
    problem_category: Optional[str] = None
    topic_category: Optional[str] = None
    problem: Optional[str] = None
    audio_s3_url: Optional[str] = None
    processing_status: Optional[str] = "pending"
    processing_message: Optional[str] = "문제가 생성되었습니다."

class TestCreationResponse(BaseModel):
    """테스트 생성 응답 모델"""
    id: str = Field(..., alias="_id")
    user_id: Optional[str] = None
    test_type: bool
    test_type_str: Optional[TestTypeEnum] = None  # 새 필드 추가
    test_date: datetime
    problem_data: Dict[str, TestCreationProblemDetail] = {}
    
    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

class SingleProblemResponse(BaseModel):
    """랜덤 단일 문제 응답 모델"""
    test_id: str
    problem_id: str
    problem_category: str
    topic_category: str
    content: str
    audio_s3_url: Optional[str] = None
    high_grade_kit: bool = False
    user_id: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "test_id": "507f1f77bcf86cd799439033",
                "problem_id": "507f1f77bcf86cd799439011",
                "problem_category": "short_conversation",
                "topic_category": "listening",
                "content": "What does the woman suggest about the report?",
                "audio_s3_url": "https://example-bucket.s3.amazonaws.com/audio/problem123.mp3",
                "high_grade_kit": True,
                "user_id": "507f1f77bcf86cd799439022"
            }
        }
    }


class ProblemFeedbackDetail(BaseModel):
    """랜덤 문제 피드백 상세 정보"""
    paragraph: Optional[str] = None
    vocabulary: Optional[str] = None
    spoken_amount: Optional[str] = None

class RandomProblemEvaluationResponse(BaseModel):
    """랜덤 문제 평가 응답 모델"""
    problem_id: str
    user_id: str
    problem_category: str
    topic_category: str
    problem_content: str
    transcribed_text: str
    score: str
    feedback: ProblemFeedbackDetail
    evaluated_at: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "problem_id": "507f1f77bcf86cd799439011",
                "user_id": "507f1f77bcf86cd799439022",
                "problem_category": "묘사",
                "topic_category": "주거",
                "problem_content": "현재 살고 있는 곳에 대해 설명해주세요.",
                "transcribed_text": "I live in an apartment in Seoul...",
                "score": "IH",
                "feedback": {
                    "paragraph": "논리적 구성이 잘 되어 있습니다.",
                    "vocabulary": "다양한 어휘를 적절히 사용했습니다.",
                    "spoken_amount": "충분한 발화량을 보여주었습니다."
                },
                "evaluated_at": "2023-10-15T09:30:00.123456"
            }
        }
    }

# 테스트 결과 업데이트를 위한 요청 모델
class ProblemDetailFeedbackUpdate(BaseModel):
    """문제별 피드백 상세 정보 업데이트 모델"""
    paragraph: Optional[str] = None
    vocabulary: Optional[str] = None
    spoken_amount: Optional[str] = None

class ProblemDetailUpdate(BaseModel):
    """문제 상세 정보 업데이트 모델"""
    user_response: Optional[str] = None
    score: Optional[str] = None
    feedback: Optional[ProblemDetailFeedbackUpdate] = None
    processing_status: Optional[str] = None
    processing_message: Optional[str] = None

class ScoreDetailUpdate(BaseModel):
    """점수 상세 정보 업데이트 모델"""
    total_score: Optional[str] = None
    comboset_score: Optional[str] = None
    roleplaying_score: Optional[str] = None
    unexpected_score: Optional[str] = None

class FeedbackDetailUpdate(BaseModel):
    """피드백 상세 정보 업데이트 모델"""
    total_feedback: Optional[str] = None
    paragraph: Optional[str] = None
    vocabulary: Optional[str] = None
    spoken_amount: Optional[str] = None

class UpdateTestRequest(BaseModel):
    """테스트 결과 업데이트 요청 모델"""
    test_score: Optional[ScoreDetailUpdate] = None
    test_feedback: Optional[FeedbackDetailUpdate] = None
    problem_data: Optional[Dict[str, ProblemDetailUpdate]] = None
    overall_feedback_status: Optional[str] = None
    overall_feedback_message: Optional[str] = None