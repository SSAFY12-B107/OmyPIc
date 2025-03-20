# Backend/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any
from services import auth as auth_service

import os
from itertools import cycle
from core.config import settings

# OAuth2 스키마 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    현재 인증된 사용자 조회 의존성
    """
    user = await auth_service.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 정보가 유효하지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# API 키 순환자 초기화
_gemini_key_cycle = None
_groq_key_cycle = None

def _init_key_cycles():
    global _gemini_key_cycle, _groq_key_cycle
    
    gemini_keys = settings.gemini_api_keys_list
    groq_keys = settings.groq_api_keys_list
    
    # 순환자 생성
    _gemini_key_cycle = cycle(gemini_keys) if gemini_keys else None
    _groq_key_cycle = cycle(groq_keys) if groq_keys else None

# 초기화 실행
_init_key_cycles()

def get_next_gemini_key():
    """다음 Gemini API 키를 반환합니다."""
    if _gemini_key_cycle is None:
        raise ValueError("Gemini API 키가 설정되지 않았습니다.")
    return next(_gemini_key_cycle)

def get_next_groq_key():
    """다음 Groq API 키를 반환합니다."""
    if _groq_key_cycle is None:
        raise ValueError("Groq API 키가 설정되지 않았습니다.")
    return next(_groq_key_cycle)