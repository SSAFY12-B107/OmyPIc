from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from db.session import create_db_and_tables, get_redis
from api.auth import router as auth_router
from api.users import router as users_router

# FastAPI 앱 생성 (lifespan 컨텍스트 매니저 적용)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행할 코드 (startup)
    # 데이터베이스 초기화
    await create_db_and_tables()
    # Redis 연결 테스트
    redis_client = await get_redis()
    await redis_client.ping()
    print("Connected to Redis")
    
    yield  # 애플리케이션 실행
    
    # 종료 시 실행할 코드 (shutdown)
    print("Shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기본 라우트
@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

# 라우터 등록
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")

# 앱 실행 부분
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)