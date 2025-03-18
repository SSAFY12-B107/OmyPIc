from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
from bson import ObjectId
from pymongo.database import Database

from db.mongodb import get_mongodb
from schemas.problem import ProblemCreate, ProblemResponse

router = APIRouter()

@router.post("/", response_model=ProblemResponse, status_code=status.HTTP_201_CREATED)
async def create_problem(
    problem: ProblemCreate,
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    새 문제 생성
    """
    problem_data = problem.model_dump(exclude_unset=True)
    
    # 문제 저장
    result = await db.problems.insert_one(problem_data)
    
    # 저장된 문제 조회
    created_problem = await db.problems.find_one({"_id": result.inserted_id})
    
    if created_problem is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문제 생성 후 조회에 실패했습니다."
        )
    
    # ObjectId를 문자열로 변환
    created_problem["_id"] = str(created_problem["_id"])
    
    return created_problem