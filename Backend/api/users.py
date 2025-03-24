from fastapi import APIRouter, HTTPException, status, Query, Path, Body, Depends
from typing import List, Optional
from schemas.user import UserCreate, UserResponse, UserUpdate, UserDetailResponse, UserUpdateSchema
from motor.motor_asyncio import AsyncIOMotorDatabase as Database
from db.mongodb import get_mongodb

from services import user as user_service
from services import test_service
from bson import ObjectId
from datetime import datetime
from fastapi.responses import JSONResponse

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


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(user_id: str, db = Depends(get_mongodb)):
    """
    사용자 ID로 사용자 조회 (최근 7개의 테스트 정보 포함)
    """
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 사용자 ID 형식입니다.")
    
    # 사용자 정보 조회
    user = await db.users.find_one({"_id": oid})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {user_id}인 사용자를 찾을 수 없습니다."
        )
    
    # ObjectId를 문자열로 변환
    user["_id"] = str(user["_id"])
    
    # 최근 7개의 테스트 정보 조회
    test_info = await test_service.get_test_by_user_id(db, user_id)
    
    # 테스트 정보 추가
    if test_info:
        user["test"] = test_info
    
    # 명시적으로 모델로 변환 후 리턴
    return UserDetailResponse.model_validate(user)


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0, description="건너뛸 사용자 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 사용자 수")
):
    """모든 사용자를 조회합니다."""
    users = await user_service.get_users(skip, limit)
    return users

@router.put("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def update_user_info(
    user_id: str = Path(..., description="사용자 ID"),
    user_data: UserUpdateSchema = Body(..., description="업데이트할 사용자 정보"),
    db = Depends(get_mongodb)
):
    """
    사용자 정보 수정 API
    """
    try:
        # ObjectId로 변환
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 사용자 ID 형식입니다."
        )
    
    # 사용자 존재 여부 확인
    existing_user = await db.users.find_one({"_id": user_object_id})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {user_id}인 사용자를 찾을 수 없습니다."
        )
    
    # 업데이트할 데이터 준비
    update_data = {}
    
    # 제공된 필드만 업데이트
    if user_data.target_opic_score is not None:
        update_data["target_opic_score"] = user_data.target_opic_score
        
    if user_data.current_opic_score is not None:
        update_data["current_opic_score"] = user_data.current_opic_score
        
    if user_data.target_exam_date is not None:
        # date 객체를 datetime 객체로 변환
        target_date = user_data.target_exam_date
        target_datetime = datetime.combine(target_date, datetime.min.time())
        update_data["target_exam_date"] = target_datetime

    # is_onboarded 필드 처리
    if user_data.is_onboarded is not None:
        update_data["is_onboarded"] = user_data.is_onboarded
        
    if user_data.background_survey is not None:
        # 기존 background_survey 가져오기
        existing_survey = existing_user.get("background_survey", {})
        
        # 새로운 데이터를 병합 (제공된 필드만 업데이트)
        survey_data = user_data.background_survey
        
        # 기존 데이터와 새 데이터 병합
        merged_survey = {**existing_survey, **survey_data}
        update_data["background_survey"] = merged_survey
    
    # 업데이트 시간 추가
    update_data["updated_at"] = datetime.now()
    
    # 사용자 정보 업데이트
    result = await db.users.update_one(
        {"_id": user_object_id},
        {"$set": update_data}
    )
    
    # 업데이트된 사용자 정보 조회
    updated_user = await db.users.find_one({"_id": user_object_id})
    
    # MongoDB 문서를 API 응답 형식으로 변환
    response_data = dict(updated_user)
    response_data["id"] = str(updated_user["_id"])  # _id를 id로 변환
    del response_data["_id"]  # 원래의 _id 필드 제거
    
    return response_data

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