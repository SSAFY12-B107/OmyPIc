import uuid
from fastapi import Depends

from fastapi_users import FastAPIUsers

from models.user import UserModel
from services.user_manager import get_user_manager
from core.security import auth_backend, refresh_backend

# FastAPIUsers 설정
fastapi_users = FastAPIUsers[UserModel, uuid.UUID](get_user_manager, [auth_backend, refresh_backend])

# 현재 인증된 사용자 의존성
current_active_user = fastapi_users.current_user(active=True)