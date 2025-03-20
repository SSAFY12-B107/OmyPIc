from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import logging

from api import problems_api, tests_api
from api import auth, users
from core.config import settings
from db.mongodb import connect_to_mongo, close_mongo_connection

from prometheus_client import Summary, make_asgi_app
from starlette.middleware.base import BaseHTTPMiddleware

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus 메트릭 설정 (API 요청 시간 측정)
# REQUEST_TIME = Summary("request_processing_seconds", "Time spent processing request")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("앱 시작함.")
    
    # MongoDB 연결 설정
    await connect_to_mongo()
    
    # MongoDB 인덱스 생성
    await setup_mongo_indexes()
    
    yield  # 애플리케이션 실행
    
    # MongoDB 연결 종료
    await close_mongo_connection()
    
    print("Shutting down...")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 요청 시간 로깅 + Prometheus 메트릭 수집 미들웨어 추가
@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Prometheus 메트릭 기록
    # REQUEST_TIME.observe(process_time)
    
    # 로깅
    logger.info(f"URL: {request.url.path}, Time taken: {process_time:.4f} seconds")
    
    return response


# Prometheus 메트릭 엔드포인트 추가 (/metrics)
# app.mount("/metrics", make_asgi_app())

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
