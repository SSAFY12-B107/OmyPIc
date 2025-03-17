from fastapi import APIRouter, HTTPException, status, Query, Body
from typing import List, Optional
from schemas.user import UserCreate, UserResponse, UserUpdate
from services import user as user_service

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate):
    """
    새 사용자 생성 엔드포인트
    """
    # 백그라운드 서베이 정보 준비
    background_survey = None
    if user_data.background_survey:
        background_survey = user_data.background_survey.dict(exclude_unset=True)
    
    user = await user_service.create_user(
        name=user_data.name,
        auth_provider=user_data.auth_provider,
        current_opic_score=user_data.current_opic_score,
        target_opic_score=user_data.target_opic_score,
        target_exam_date=user_data.target_exam_date,
        background_survey=background_survey
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="사용자 생성에 실패했습니다."
        )
    
    return user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """
    사용자 ID로 사용자 조회 엔드포인트
    """
    user = await user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {user_id}인 사용자를 찾을 수 없습니다."
        )
    
    return user

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(10, ge=1, le=100, description="가져올 최대 항목 수")
):
    """
    사용자 목록 조회 엔드포인트
    """
    users = await user_service.get_users(skip, limit)
    return users

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate = Body(...)
):
    """
    사용자 정보 부분 업데이트 엔드포인트
    
    PATCH 메서드를 사용하여 제공된 필드만 업데이트합니다.
    """
    # 업데이트할 데이터 준비 (None이 아닌 값만 포함)
    update_data = user_data.dict(exclude_unset=True)
    
    # 백그라운드 서베이 정보 처리
    if "background_survey" in update_data and update_data["background_survey"]:
        update_data["background_survey"] = update_data["background_survey"].dict(exclude_unset=True)
    
    # 사용자 업데이트
    updated_user = await user_service.update_user(user_id, update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {user_id}인 사용자를 찾을 수 없습니다."
        )
    
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    """
    사용자 삭제 엔드포인트
    """
    deleted = await user_service.delete_user(user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {user_id}인 사용자를 찾을 수 없습니다."
        )
    
    return None