from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
from bson import ObjectId
from pymongo.database import Database
from datetime import datetime

from db.mongodb import get_mongodb
from schemas.script import ScriptCreate, ScriptResponse

router = APIRouter()

@router.post("/", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
async def create_script(
    script: ScriptCreate,
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    새 스크립트 생성 (컬렉션 생성 확인용)
    """
    script_data = script.model_dump(exclude_unset=True)
    
    # created_at 필드 추가
    script_data["created_at"] = datetime.now()
    
    # 스크립트 저장
    result = await db.scripts.insert_one(script_data)
    
    # 저장된 스크립트 조회
    created_script = await db.scripts.find_one({"_id": result.inserted_id})
    
    if created_script is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="스크립트 생성 후 조회에 실패했습니다."
        )
    
    # ObjectId를 문자열로 변환
    created_script["_id"] = str(created_script["_id"])
    
    return created_script