from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

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
    type: str  # "basic" 또는 "custom"
    basic_answers: QuestionAnswers  # 기본 질문에 대한 응답 (항상 필수)
    custom_answers: Optional[QuestionAnswers] = None  # 커스텀 질문에 대한 응답 (커스텀 타입일 때만 필수)
    
    @field_validator('type')
    @classmethod  # classmethod 데코레이터 필요
    def validate_type(cls, v):
        if v not in ["basic", "custom"]:
            raise ValueError("스크립트 타입은 'basic' 또는 'custom'이어야 합니다.")
        return v
    
    @field_validator('custom_answers')
    @classmethod  # classmethod 데코레이터 필요
    def validate_custom_answers(cls, v, info):
        # Pydantic v2에서는 values 대신 info.data 사용
        if 'type' in info.data and info.data['type'] == 'custom' and v is None:
            raise ValueError("커스텀 타입에는 custom_answers가 필요합니다.")
        return v


# 스크립트 생성 모델
class ScriptCreationResponse(BaseModel):
    id: str = Field(..., alias="_id")
    content: str
    created_at: datetime
    is_script: bool

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