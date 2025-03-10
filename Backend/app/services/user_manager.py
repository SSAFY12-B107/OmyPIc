import uuid
from typing import Optional

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import select

from fastapi_users import UUIDIDMixin
from fastapi_users.manager import BaseUserManager
from fastapi_users.db import SQLAlchemyUserDatabase

from models.user import UserModel, SocialAccount
from db.session import get_async_session
from core.config import settings

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, UserModel)

# User Manager 설정
class UserManager(UUIDIDMixin, BaseUserManager[UserModel, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(self, user: UserModel, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: UserModel, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: UserModel, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

    async def create_social_user(
        self,
        provider: str,
        social_id: str,
        social_email: str,
        name: str,
    ) -> UserModel:
        """소셜 인증으로 사용자 생성"""
        
        # 동일 이메일로 다른 소셜에서 가입된 계정이 있는지 확인
        existing_account = await self.user_db.session.execute(
            select(SocialAccount).where(SocialAccount.social_email == social_email)
        )
        existing_account = existing_account.scalar_one_or_none()
        
        if existing_account:
            # 동일 이메일로 다른 소셜에서 가입된 계정이 있을 경우
            # 해당 유저를 가져옴
            user_query = await self.user_db.session.execute(
                select(UserModel).where(UserModel.id == existing_account.user_id)
            )
            user = user_query.scalar_one_or_none()
            
            # 새로운 소셜 계정을 기존 유저에 연결
            social_account = SocialAccount(
                id=str(uuid.uuid4()),
                user_id=str(user.id),
                provider=provider,
                social_id=social_id,
                social_email=social_email
            )
            self.user_db.session.add(social_account)
            await self.user_db.session.commit()
            
            return user
        else:
            # 신규 유저 생성
            user_dict = {
                "email": social_email,
                "hashed_password": self.password_helper.hash(""),  # 빈 비밀번호
                "name": name,
                "auth_provider": provider,
                "is_active": True,
                "is_superuser": False,
                "is_verified": True,  # 소셜 인증은 이미 검증된 것으로 간주
                "is_onboarded": False,  # 초기 설문 미완료 상태
            }
            
            # 새 유저 생성
            user = UserModel(**user_dict)
            self.user_db.session.add(user)
            await self.user_db.session.commit()
            await self.user_db.session.refresh(user)
            
            # 소셜 계정 정보 저장
            social_account = SocialAccount(
                id=str(uuid.uuid4()),
                user_id=str(user.id),
                provider=provider,
                social_id=social_id,
                social_email=social_email
            )
            self.user_db.session.add(social_account)
            await self.user_db.session.commit()
            
            return user

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)