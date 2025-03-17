from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import UserModel
from db.session import get_async_session
from services.auth import current_active_user

# 현재 활성 사용자 의존성 - 활성 상태의 로그인 사용자를 요구
CurrentUser = Annotated[UserModel, Depends(current_active_user)]

# 온보딩 완료 사용자 의존성 - 온보딩을 완료한 사용자를 요구
async def get_onboarded_user(user: CurrentUser) -> UserModel:
    """
    사용자가 온보딩을 완료했는지 확인하는 의존성
    온보딩을 완료하지 않은 사용자는 401 Unauthorized 에러 반환
    """
    if not user.is_onboarded:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has not completed onboarding process",
        )
    return user

OnboardedUser = Annotated[UserModel, Depends(get_onboarded_user)]

# 관리자 사용자 의존성 - 관리자 권한을 가진 사용자를 요구
async def get_admin_user(user: CurrentUser) -> UserModel:
    """
    사용자가 관리자인지 확인하는 의존성
    관리자가 아닌 사용자는 403 Forbidden 에러 반환
    """
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user

AdminUser = Annotated[UserModel, Depends(get_admin_user)]

# 사용자와 DB 세션을 함께 주입받는 의존성
async def get_user_and_db(
    user: CurrentUser,
    db: AsyncSession = Depends(get_async_session)
) -> tuple[UserModel, AsyncSession]:
    """
    현재 로그인한 사용자와 DB 세션을 함께 반환하는 의존성
    DB 작업이 필요한 엔드포인트에서 사용
    """
    return user, db

UserAndDB = Annotated[tuple[UserModel, AsyncSession], Depends(get_user_and_db)]