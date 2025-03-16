from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
# from api.auth import router as auth_router
from api.users import router as users_router

from db.mongodb import connect_to_mongo, close_mongo_connection, mongo_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("앱 시작함.")
    
    # MongoDB 연결 설정
    await connect_to_mongo()
    
    # MongoDB 인덱스 생성
    await setup_mongodb_indexes()
    
    yield  # 애플리케이션 실행
    
    # MongoDB 연결 종료
    await close_mongo_connection()
    
    print("Shutting down...")

async def setup_mongodb_indexes():
    """필요한 MongoDB 인덱스를 설정합니다."""
    db = mongo_db.db
    
    # 사용자 컬렉션 인덱스
    # await db.users.create_index("email", unique=True)
    # await db.users.create_index("username")
    # await db.users.create_index([("social_accounts.provider", 1), 
    #                             ("social_accounts.provider_user_id", 1)])
    
    # # 문제 컬렉션 인덱스
    # await db.problems.create_index("category")
    # await db.problems.create_index("problem_type")
    # await db.problems.create_index([("content", "text")])
    # await db.problems.create_index("related_problems")
    
    # # 테스트 컬렉션 인덱스
    # await db.tests.create_index("user_id")
    # await db.tests.create_index("test_type")
    # await db.tests.create_index("test_title")
    
    print("MongoDB 인덱스가 생성되었습니다.")


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
# app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")

# 앱 실행 부분
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)