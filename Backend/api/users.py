from fastapi import APIRouter, HTTPException, status, Query, Path, Body, Depends
from typing import List, Optional
from schemas.user import UserCreate, UserResponse, UserUpdate
from services import user as user_service
from bson import ObjectId
import datetime

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate = Body(...)):
    """새 사용자를 생성합니다."""
    # 백그라운드 서베이 데이터 처리
    background_survey = None
    if user_data.background_survey:
        background_survey = user_data.background_survey.dict(exclude_unset=True)
    
    # 시험 날짜 처리
    if user_data.target_exam_date:
        target_exam_date = user_data.target_exam_date
    else:
        target_exam_date = None
    
    # 사용자 생성
    user = await user_service.create_user(
        name=user_data.name,
        auth_provider=user_data.auth_provider,
        current_opic_score=user_data.current_opic_score,
        target_opic_score=user_data.target_opic_score,
        target_exam_date=target_exam_date,
        background_survey=background_survey
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="사용자 생성에 실패했습니다."
        )
    
    return user

@router.get("/{user_id}", response_model=UserResponse)
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """
    사용자 ID로 사용자 조회 엔드포인트
    """
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 사용자 ID 형식입니다.")
    
    user = await user_service.get_user_by_id(oid)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {id}인 사용자를 찾을 수 없습니다."
        )
    
    return user

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0, description="건너뛸 사용자 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 사용자 수")
):
    """모든 사용자를 조회합니다."""
    users = await user_service.get_users(skip, limit)
    return users

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate = Body(...)
):
    """
    사용자 정보 부분 업데이트 엔드포인트
    
    PATCH 메서드를 사용하여 제공된 필드만 업데이트합니다.
    """
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 사용자 ID 형식입니다.")
    
    # 업데이트할 데이터 준비 (None이 아닌 값만 포함)
    update_data = user_data.dict(exclude_unset=True)
    
    # 백그라운드 서베이 데이터 처리
    if "background_survey" in update_data and update_data["background_survey"]:
        update_data["background_survey"] = update_data["background_survey"].dict(exclude_unset=True)
    
    # 사용자 업데이트
    updated_user = await user_service.update_user(oid, update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {id}인 사용자를 찾을 수 없습니다."
        )
    
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    """
    사용자 삭제 엔드포인트
    """
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 사용자 ID 형식입니다.")
    
    deleted = await user_service.delete_user(oid)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {id}인 사용자를 찾을 수 없습니다."
        )
    
    return None

async def get_user_by_id(user_id: str):
    # MongoDB를 사용하는 경우 (로그를 보면 MongoDB를 사용하고 있음)
    from db.mongodb import db
    
    user = await db.users.find_one({"_id": user_id})
    return user