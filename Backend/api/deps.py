from typing import Generator, Optional
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from core.config import settings
from db.mongodb import connect_to_mongo



async def get_db():
    """MongoDB 데이터베이스 세션 의존성"""
    db = await connect_to_mongo()
    try:
        yield db
    finally:
        # Motor는 자동으로 연결을 관리하므로 명시적 닫기가 필요 없음
        pass