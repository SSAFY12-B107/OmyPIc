from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    기본 로그인 엔드포인트 (아직 실제 구현은 되지 않음)
    """
    # 여기서는 임시 토큰만 반환
    # 실제 구현에서는 사용자 인증 후 JWT 토큰 생성
    return {
        "access_token": "dummy_token",
        "token_type": "bearer"
    }

@router.post("/register")
async def register():
    """
    사용자 등록 엔드포인트 (아직 실제 구현은 되지 않음)
    """
    return {"message": "사용자 등록 기능은 아직 구현되지 않았습니다."}