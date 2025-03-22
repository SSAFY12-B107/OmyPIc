from pydantic import BaseModel, Field
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


# 스크립트 기본 질문 응답 모델
class BasicQuestionResponse(BaseModel):
    content: str
    questions: List[str]


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