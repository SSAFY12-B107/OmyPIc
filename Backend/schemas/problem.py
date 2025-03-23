from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# 기존 스키마 클래스들...

class ProblemResponse(BaseModel):
    """문제 응답 스키마(전체 조회)"""
    id: str = Field(..., alias="_id")
    topic_category: str
    problem_category: str
    content: str    

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "topic_category": "listening",
                "problem_category": "short_conversation",
                "content": "What does the woman suggest about the report?",
            }
        }
    }

# 다수의 문제 목록을 위한 응답 스키마
class ProblemListResponse(BaseModel):
    problems: List[ProblemResponse]
    total: int

class ProblemDetailContentResponse(BaseModel):
    """문제 응답 스키마(개별 조회 시, 문제 내용)"""
    id: str = Field(..., alias="_id")
    content: str

# 문제 세부 조회 응답 모델
class ProblemDetailScriptResponse(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    content: str
    created_at: datetime
    is_script: bool

class ProblemDetailResponse(BaseModel):
    """문제 응답 스키마(개별 조회)"""
    problem: ProblemDetailContentResponse
    user_scripts: Optional[List[ProblemDetailScriptResponse]] = []
    test_notes: Optional[List[ProblemDetailScriptResponse]] = []


# 스크립트 기본/꼬리 질문 응답 모델
class QuestionResponse(BaseModel):
    content: str
    questions: List[str]


# 스크립트 꼬리 질문 요청/응답 모델
class CustomQuestionRequest(BaseModel):
    question1: str
    question2: str
    question3: str


# 질문에 대한 응답 모델 (기본 및 커스텀 공통)
class QuestionAnswers(BaseModel):
    answer1: str
    answer2: str
    answer3: str


# 스크립트 생성 요청 모델
class ScriptCreationRequest(BaseModel):
    type: str  # "basic", "custom" 또는 "opic"
    basic_answers: QuestionAnswers  # 기본 질문에 대한 응답 (항상 필수)
    custom_answers: Optional[QuestionAnswers] = None  # 커스텀 질문에 대한 응답 (커스텀 타입일 때만 필수)
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v not in ["basic", "custom", "opic"]:
            raise ValueError("스크립트 타입은 'basic', 'custom' 또는 'opic'이어야 합니다.")
        return v
    
    @field_validator('custom_answers')
    @classmethod
    def validate_custom_answers(cls, v, info):
        # Pydantic v2에서는 values 대신 info.data 사용
        if 'type' in info.data and info.data['type'] == 'custom' and v is None:
            raise ValueError("커스텀 타입에는 custom_answers가 필요합니다.")
        return v

# 스크립트 생성 모델
class ScriptCreationResponse(BaseModel):
    _id: str
    content: str
    created_at: datetime
    is_script: bool
    script_type: str
    
    class Config:
        populate_by_name = True

# 스크립트 응답 모델
class ScriptResponse(BaseModel):
    id: str = Field(..., alias="_id")
    content: str
    created_at: datetime
    is_script: bool

    class Config:
        populate_by_name = True

# 스크립트 업데이트를 위한 요청 모델
class ScriptUpdateRequest(BaseModel):
    content: str = Field(..., description="수정할 스크립트 내용")


# --- OPIc 스크립트 생성 관련 스키마 추가 ---

# OPIc 스크립트 생성을 위한 답변 항목
class OPIcAnswerItem(BaseModel):
    answer1: str = Field(default="", description="첫 번째 질문에 대한 답변")
    answer2: str = Field(default="", description="두 번째 질문에 대한 답변")
    answer3: str = Field(default="", description="세 번째 질문에 대한 답변")

    model_config = {
        "json_schema_extra": {
            "example": {
                "answer1": "저는 한강 근처에 살고 있어요. 강가에 산책로가 있어서 걷기 좋아요.",
                "answer2": "한강의 야경이 특히 아름다워요. 밤에 보는 다리의 불빛이 인상적이에요.",
                "answer3": "평화로운 휴식처라고 표현할 수 있어요. 도시 속 자연을 느낄 수 있거든요."
            }
        }
    }

# OPIc 스크립트 생성 요청 모델
class OPIcScriptRequest(BaseModel):
    type: str = Field(..., description="질문 유형 (description, past_experience, routine, comparison, roleplaying)")
    basic_answers: OPIcAnswerItem = Field(..., description="기본 답변")
    custom_answers: OPIcAnswerItem = Field(..., description="사용자 정의 답변")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        valid_types = ["description", "past_experience", "routine", "comparison", "roleplaying"]
        if v not in valid_types:
            raise ValueError(f"질문 유형은 {', '.join(valid_types)} 중 하나여야 합니다.")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "description",
                "basic_answers": {
                    "answer1": "저는 한강 근처에 살고 있어요. 강가에 산책로가 있어서 걷기 좋아요.",
                    "answer2": "한강의 야경이 특히 아름다워요. 밤에 보는 다리의 불빛이 인상적이에요.",
                    "answer3": "평화로운 휴식처라고 표현할 수 있어요. 도시 속 자연을 느낄 수 있거든요."
                },
                "custom_answers": {
                    "answer1": "",
                    "answer2": "",
                    "answer3": ""
                }
            }
        }
    }

# OPIc 스크립트 생성 응답 모델
class OPIcScriptResponse(BaseModel):
    script: str = Field(..., description="생성된 OPIc 스크립트")
    status: str = Field(..., description="생성 상태 (success, error)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "script": "Well, I'd like to talk about where I live near the Han River. It's actually a really nice area with walking paths along the riverside that make it perfect for taking a stroll. You know, what I find most impressive about this place is the night view, especially the lights on the bridges that reflect on the water. When I have friends visiting Seoul, I always make sure to take them there because it's such a spectacular sight. I've been living in this neighborhood for about two years now, and I've grown to appreciate the peaceful atmosphere despite being in the middle of a busy city. I mean, it's amazing how you can feel so connected to nature while still being in an urban environment. Overall, I'd describe it as a peaceful sanctuary - a place where I can escape from the hustle and bustle of city life whenever I need to recharge.",
                "status": "success"
            }
        }
    }

    # 스크립트 생성 요청 모델 - schemas/problem.py 파일에 있는 기존 모델 업데이트
class ScriptCreationRequest(BaseModel):
    type: str  # "basic", "custom" 또는 "opic"
    basic_answers: QuestionAnswers  # 기본 질문에 대한 응답 (항상 필수)
    custom_answers: Optional[QuestionAnswers] = None  # 커스텀 질문에 대한 응답 (커스텀 타입일 때만 필수)
    
    @field_validator('type')
    @classmethod  # classmethod 데코레이터 필요
    def validate_type(cls, v):
        if v not in ["basic", "custom", "opic"]:
            raise ValueError("스크립트 타입은 'basic', 'custom' 또는 'opic'이어야 합니다.")
        return v
    
    @field_validator('custom_answers')
    @classmethod  # classmethod 데코레이터 필요
    def validate_custom_answers(cls, v, info):
        # Pydantic v2에서는 values 대신 info.data 사용
        if 'type' in info.data and info.data['type'] == 'custom' and v is None:
            raise ValueError("커스텀 타입에는 custom_answers가 필요합니다.")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "basic",
                "basic_answers": {
                    "answer1": "한국어 답변 1",
                    "answer2": "한국어 답변 2",
                    "answer3": "한국어 답변 3"
                },
                "custom_answers": {
                    "answer1": "커스텀 답변 1",
                    "answer2": "커스텀 답변 2",
                    "answer3": "커스텀 답변 3"
                }
            }
        }
    }