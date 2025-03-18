from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
from bson import ObjectId
from pymongo.database import Database

from db.mongodb import get_mongodb
from schemas.question import QuestionCreate, QuestionResponse

router = APIRouter()

@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    question: QuestionCreate,
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    새 질문 생성 (컬렉션 생성 확인용)
    """
    question_data = question.model_dump(exclude_unset=True)
    
    # 질문 저장
    result = await db.questions.insert_one(question_data)
    
    # 저장된 질문 조회
    created_question = await db.questions.find_one({"_id": result.inserted_id})
    
    if created_question is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="질문 생성 후 조회에 실패했습니다."
        )
    
    # ObjectId를 문자열로 변환
    created_question["_id"] = str(created_question["_id"])
    
    return created_question