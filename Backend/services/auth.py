from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import jwt
from passlib.context import CryptContext

from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    pass 

def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    pass


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """JWT 액세스 토큰 생성"""

    pass 