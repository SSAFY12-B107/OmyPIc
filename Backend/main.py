from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from scripts.scheduler import setup_scheduler

import time
import logging

from api import problems_api, tests_api
from api import auth, users
from core.config import settings
from db.mongodb import connect_to_mongo, close_mongo_connection

# 요청 본문 크기 제한 설정
from starlette.middleware.base import BaseHTTPMiddleware

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("앱 시작함.")
    
    # MongoDB 연결 설정
    await connect_to_mongo()
    
    # MongoDB 인덱스 생성
    await setup_mongo_indexes()
    
    # 스케줄러 설정 및 시작
    app.state.scheduler = setup_scheduler()
    app.state.scheduler.start()
    logger.info("스케줄러가 시작되었습니다.")

    yield  # 애플리케이션 실행
    
    # 스케줄러 종료
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()
        logger.info("스케줄러가 종료되었습니다.")

    # MongoDB 연결 종료
    await close_mongo_connection()
    
    print("앱 종료됨")

async def setup_mongo_indexes():
    """필요한 MongoDB 인덱스를 설정합니다."""
    print("MongoDB 인덱스가 생성되었습니다.")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request._body_size_limit = 15 * 1024 * 1024  # 15MB
        response = await call_next(request)
        return response

app.add_middleware(MaxBodySizeMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Error-Type"]  # 커스텀 헤더 노출 설정 추가
)

# 요청 시간 로깅
@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # 로깅
    logger.info(f"URL: {request.url.path}, Time taken: {process_time:.4f} seconds")
    
    return response


# 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["인증"])
app.include_router(users.router, prefix="/api/users", tags=["사용자"])
app.include_router(tests_api.router, prefix="/api/tests", tags=["모의고사"])
app.include_router(problems_api.router, prefix="/api/problems", tags=["문제"])


@app.get("/")
async def root():
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "message": "OmyPIC API 서비스에 오신 것을 환영합니다!"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
