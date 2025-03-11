from typing import Dict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import UserModel
from db.session import get_async_session
from api.deps import CurrentUser, UserAndDB
from schemas.user import OnboardingData, UserResponse

router = APIRouter(tags=["users"], prefix="/users")

@router.get("/me", response_model=UserResponse)
async def get_user_profile(user: CurrentUser):
    """현재 로그인한 사용자 정보 반환"""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        current_opic_score=user.current_opic_score,
        target_opic_score=user.target_opic_score,
        target_exam_date=user.target_exam_date,
        expected_opic_score=user.expected_opic_score,
        is_active=user.is_active,
        is_onboarded=user.is_onboarded,
        auth_provider=user.auth_provider
    )

@router.post("/onboarding", response_model=UserResponse)
async def complete_onboarding(
    onboarding_data: OnboardingData,
    user_and_db: UserAndDB,
):
    """
    사용자 온보딩 정보(초기 설문) 저장
    
    요구되는 데이터:
    - target_opic_score: 목표 오픽 성적
    - expected_opic_score: 예상 오픽 성적
    - current_opic_score: (선택) 현재 오픽 성적
    - target_exam_date: (선택) 목표 시험 일자
    """
    user, db = user_and_db
    
    # 사용자 정보 업데이트
    user.target_opic_score = onboarding_data.target_opic_score
    user.expected_opic_score = onboarding_data.expected_opic_score
    
    # 선택적 정보 업데이트
    if onboarding_data.current_opic_score:
        user.current_opic_score = onboarding_data.current_opic_score
    
    if onboarding_data.target_exam_date:
        # 날짜 문자열을 Date 객체로 변환 (YYYY-MM-DD 형식 가정)
        try:
            target_date = datetime.strptime(onboarding_data.target_exam_date, "%Y-%m-%d").date()
            user.target_exam_date = target_date
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Expected YYYY-MM-DD"
            )
    
    # 온보딩 완료 상태로 업데이트
    user.is_onboarded = True
    
    # 변경사항 저장
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 업데이트된 사용자 정보 반환
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        current_opic_score=user.current_opic_score,
        target_opic_score=user.target_opic_score,
        target_exam_date=user.target_exam_date,
        expected_opic_score=user.expected_opic_score,
        is_active=user.is_active,
        is_onboarded=user.is_onboarded,
        auth_provider=user.auth_provider
    )

@router.patch("/update-profile", response_model=UserResponse)
async def update_user_profile(
    user_data: Dict,
    user_and_db: UserAndDB,
):
    """사용자 프로필 정보 업데이트"""
    user, db = user_and_db
    
    # 업데이트 가능한 필드 목록
    updatable_fields = [
        "name", 
        "current_opic_score", 
        "target_opic_score", 
        "expected_opic_score"
    ]
    
    # 요청 데이터에서 업데이트 가능한 필드만 추출하여 사용자 정보 업데이트
    for field in updatable_fields:
        if field in user_data:
            setattr(user, field, user_data[field])
    
    # 날짜 필드 처리
    if "target_exam_date" in user_data and user_data["target_exam_date"]:
        try:
            target_date = datetime.strptime(user_data["target_exam_date"], "%Y-%m-%d").date()
            user.target_exam_date = target_date
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Expected YYYY-MM-DD"
            )
    
    # 변경사항 저장
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 업데이트된 사용자 정보 반환
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        current_opic_score=user.current_opic_score,
        target_opic_score=user.target_opic_score,
        target_exam_date=user.target_exam_date,
        expected_opic_score=user.expected_opic_score,
        is_active=user.is_active,
        is_onboarded=user.is_onboarded,
        auth_provider=user.auth_provider
    )