from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import auth, users
from core.config import settings
from db.mongodb import connect_to_mongo, close_mongo_connection

# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION
)

# CORS 미들웨어 설정
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 시작 이벤트에 MongoDB 연결 설정
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

# 종료 이벤트에 MongoDB 연결 종료
@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["인증"])
app.include_router(users.router, prefix="/api/users", tags=["사용자"])

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