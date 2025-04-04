from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# 테스트 유형 열거형 정의
class TestTypeEnum(str, Enum):
    FULL_TEST = "full_test"        # 실전 모의고사 (15문제)
    CATEGORICAL_TEST = "category"  # 유형별 테스트 (3문제)
    SINGLE_PROBLEM = "single"      # 랜덤 1문제
    HALF_TEST = "half_test"        # 기존 half_test 식별용

class ScoreDetail(BaseModel):
    """점수 상세 정보 모델"""
    total_score: Optional[str] = None
    comboset_score: Optional[str] = None
    roleplaying_score: Optional[str] = None
    unexpected_score: Optional[str] = None

class FeedbackDetail(BaseModel):
    """피드백 상세 정보 모델"""
    total_feedback: Optional[str] = None
    paragraph: Optional[str] = None
    vocabulary: Optional[str] = None
    spoken_amount: Optional[str] = None

class ProblemDetailFeedback(BaseModel):
    """문제별 피드백 상세 정보 모델"""
    paragraph: Optional[str] = None
    vocabulary: Optional[str] = None
    spoken_amount: Optional[str] = None


class ProblemDetail(BaseModel):
    """문제 상세 정보 모델"""
    problem_id: Optional[str] = None  # 문제 ID
    problem_category: Optional[str] = None  # 문제 카테고리
    topic_category: Optional[str] = None  # 문제 카테고리
    problem: Optional[str] = None  # 문제 내용 
    audio_s3_url: Optional[str] = None
    user_response: Optional[str] = None  # 사용자 응답
    score: Optional[str] = None  # 점수
    feedback: Optional[ProblemDetailFeedback] = None  # 피드백 (단일 객체)


class TestModel(BaseModel):
    """테스트(모의고사) 모델"""
    id: Optional[str] = Field(default=None, alias="_id")  # MongoDB의 _id를 문자열로 표현
    test_type: bool  # 테스트 유형 (False: Full, True: Half(속성))
    test_type_str: Optional[TestTypeEnum] = None  # 새로운 열거형 필드 추가
    test_score: Optional[ScoreDetail] = None  # 테스트 점수 정보
    test_feedback: Optional[FeedbackDetail] = None  # 테스트 피드백 정보
    problem_data: Dict[str, ProblemDetail] = Field(default_factory=dict)  # 문제 번호를 키로 하는 문제 상세 정보 (문자열 키 사용)
    test_date: datetime = Field(default_factory=datetime.now)  # 테스트 날짜
    user_id: Optional[str] = None  # 사용자 ID(MongoDB ObjectId를 문자열로 표현)
    
    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "test_type": False,
                "test_type_str": "full_test",
                "test_score": {
                    "total_score": "IH",
                    "comboset_score": "AL",
                    "roleplaying_score": "IH",
                    "unexpected_score": "IM2"
                },
                "test_feedback": {
                    "total_feedback": "전반적으로 양호한 성과를 보였습니다.",
                    "paragraph": "논리적 구성이 잘 되어 있습니다.",
                    "spoken_amount": "적절한 발화량을 유지했습니다.",
                    "vocabulary": "다양한 어휘를 사용했습니다."
                },
                "problem_data": {
                    "1": {
                        "problem_id": "507f1f77bcf86cd799439123",
                        "problem_category": "묘사",
                        "topic_category": "주거",
                        "problem": "자기소개를 해보세요.",
                        "audio_s3_url": "https://example-bucket.s3.amazonaws.com/audio/problem123.mp3",
                        "user_response": "안녕하세요. 저는...",
                        "score": "IH",
                        "feedback": {
                            "paragraph": "잘 구성됨",
                            "vocabulary": "다양한 어휘 사용",
                            "spoken_amount": "적절함"
                        }
                    }
                },
                "user_id": "507f1f77bcf86cd799439022",
                "test_date": "2023-10-15T09:30:00"
            }
        }
    }

    def __init__(self, **data):
        """
        기존 test_type과 새 test_type_str 필드 간 일관성 유지
        """
        super().__init__(**data)
        
        # 초기화 시 test_type_str이 없고 test_type만 있으면 test_type_str 설정
        if self.test_type_str is None and "test_type" in data:
            self.test_type_str = self._bool_to_test_type(self.test_type)
        
        # 초기화 시 test_type이 없고 test_type_str만 있으면 test_type 설정
        elif "test_type" not in data and self.test_type_str is not None:
            self.test_type = self._test_type_to_bool(self.test_type_str)
    
    def _bool_to_test_type(self, test_type_bool: bool) -> TestTypeEnum:
        """bool 값을 TestTypeEnum으로 변환"""
        return TestTypeEnum.FULL_TEST if not test_type_bool else TestTypeEnum.CATEGORICAL_TEST
    
    def _test_type_to_bool(self, test_type_enum: TestTypeEnum) -> bool:
        """TestTypeEnum을 bool 값으로 변환"""
        return test_type_enum != TestTypeEnum.FULL_TEST