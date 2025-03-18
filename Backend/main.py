from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api import auth, users, tests, problems
from core.config import settings
from db.mongodb import connect_to_mongo, close_mongo_connection

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
    # db = get_mongodb.db
    
    # 사용자 컬렉션 인덱스
    # await db.users.create_index("email", unique=True)
    # await db.users.create_index("username")
    
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


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["인증"])
app.include_router(users.router, prefix="/api/users", tags=["사용자"])
app.include_router(tests.router, prefix="/api/tests", tags=["모의고사"])
app.include_router(problems.router, prefix="/api/problems", tags=["문제"])


@app.get("/")
async def root():
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "message": "OmyPIC API 서비스에 오신 것을 환영합니다!"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)