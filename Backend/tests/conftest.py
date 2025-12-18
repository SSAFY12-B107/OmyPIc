# tests/conftest.py
'''
pytest "fixtures"를 모아두는 파일

 fixture란?
 - 테스트에 필요한 재료를 미리 준비해두는 것
 - 예: 가짜 데이터베이스, 테스트용 사용자, 가짜 HTTP 응답

 왜 conftest.py인가?
 - pytest가 자동으로 이 파일을 찾아서 읽어요
 - 여러 테스트 파일에서 공유할 수 있어요
'''

import pytest
import os
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    '''
    테스트 환경 변수 설정

    모든 테스트 실행 전에 자동으로 실행됨 (autouse=True)
    session scope로 테스트 세션당 1번만 실행됨
    '''
    # .env 파일 비활성화 (테스트 환경에서는 사용 안 함)
    os.environ["PYDANTIC_SETTINGS_DOTENV_ENABLED"] = "0"

    # 필수 환경변수 설정 (Settings 검증 통과용)
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "15"
    os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
    os.environ["WIT_AI_API_KEY"] = "test_wit_api_key"
    os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
    os.environ["JWT_SECRET_KEY"] = "test_jwt_secret"
    os.environ["REFRESH_TOKEN_SECRET_KEY"] = "test_refresh_secret"
    os.environ["AWS_ACCESS_KEY_ID"] = "test_aws_key"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test_aws_secret"
    os.environ["AWS_REGION"] = "ap-northeast-2"
    os.environ["AWS_S3_BUCKET_NAME"] = "test-bucket"

    yield

    # 테스트 종료 후 정리 (필요시)


@pytest.fixture
def mock_db():
    '''
    fake MongoDB fixture

    How to Use:
        def test_something(mock_db):
            # mock_db가 자동으로 주입됨
            mock_db.users.find_one(...)
    '''
    # db = MagicMock() db인척하는 가짜 객체
    # 주의: MagicMock 뒤에 괄호()를 붙여야 인스턴스가 생성됨!
    db = MagicMock()


    # users 컬렉션의 기본동작설정
    db.users = MagicMock()
    # 왜 여기만 AsyncMock 이냐면 FastAPI에서 붙일떄 우리는 이걸 거의 100% 비동기로 구현할거니까 async도 되는 AsyncMock()을 사용해야함
    '''
    프로세스 1개
     └── 쓰레드 1개
      └── 이벤트 루프
           ├── Task A
           ├── Task B
           └── Task C
    '''

    db.users.find_one = AsyncMock(return_value=None)
    db.users.insert_one = AsyncMock()
    db.users.update_one = AsyncMock()

    # temp_codes 컬렉션 (OAuth 임시 코드)
    db.temp_codes = MagicMock()  # 이 줄이 빠져있었음!
    db.temp_codes.find_one = AsyncMock(return_value=None)
    db.temp_codes.insert_one = AsyncMock()
    db.temp_codes.delete_one = AsyncMock()
    db.temp_codes.create_index = AsyncMock()

    # used_codes 컬렉션
    db.used_codes = MagicMock()
    db.used_codes.find_one = AsyncMock(return_value=None)
    db.used_codes.insert_one = AsyncMock()
    db.used_codes.update_one = AsyncMock()
    db.used_codes.create_index = AsyncMock()

    # token_blacklist 컬렉션 (무효화된 토큰)
    db.token_blacklist = MagicMock()
    db.token_blacklist.find_one = AsyncMock(return_value=None)  # finde_one 오타 수정!
    db.token_blacklist.insert_one = AsyncMock()
    db.token_blacklist.create_index = AsyncMock()


    # oauth_states 컬렉션 (PKCE용)
    '''
    PKCE는 "Authorization Code를 가로채도 토큰으로 바꿀 수 없게 만드는 안전장치"다.

    client_secret을 숨길 수 없는 환경(모바일/SPA)에서
    Authorization Code Flow를 안전하게 쓰기 위해 추가된 검증 절차

    ❌ 상황 가정 (PKCE 없음)

    사용자가 로그인
    Authorization Server가 code=abcd 발급
    이 code가 중간에서 탈취됨
    공격자가 이 code로 token 요청
    Access Token 탈취 성공

    ⚠️ 문제점:
    code 자체가 권한 증명 수단
    client_secret이 없는 환경에서는 막을 방법이 없음
    '''

    db.oauth_states = MagicMock()
    db.oauth_states.find_one = AsyncMock(return_value=None)
    db.oauth_states.find_one_and_update = AsyncMock(return_value=None)
    db.oauth_states.insert_one = AsyncMock()
    db.oauth_states.create_index = AsyncMock()

    return db

@pytest.fixture
def sample_google_user():
    '''
    Google Oauth로 받아오는 사용자 정보 샘플

    실제 Google API 응답 형식과 동일하게 만듬
    '''
    return {
        "sub": "google_123456789",      # Google 고유 ID
        "email": "test@gmail.com",
        "name": "테스트 유저",
        "picture": "https://example.com/photo.jpg"
    }

@pytest.fixture
def sample_naver_user():
    '''
    Naver OAuth로 받아오는 사용자 정보 샘플

    Naver는 response 안에 데이터가 있음.
    '''
    return {
        "response": {
            "id": "naver_987654321",    # Naver 고유 ID
            "email": "test@naver.com",
            "name": "테스트 유저"
        }
    }

@pytest.fixture
def create_test_tokens():
    '''
    테스트용 JWT 토큰을 만들어주는 함수를 반환

    사용법:
        def test_something(create_test_tokens):
            access, refresh = create_test_tokens("user_id_123")
    '''
    import jwt
    from datetime import datetime, timedelta, timezone

    # test용 시크릿 키(실제 환경변수와 다름)
    ACCESS_SECRET = "test_access_secret_key_12345"
    REFRESH_SECRET = "test_refresh_secret_key_67890"

    def _create_tokens(user_id: str):
        now = datetime.now(timezone.utc)

        # Access Token (30분)
        access_payload = {
            "sub": user_id,
            "name": "테스트 유저",
            "auth_provider": "google",
            "exp": now + timedelta(minutes=30),
            "iat": now
        }
        access_token = jwt.encode(access_payload, ACCESS_SECRET, algorithm="HS256")

        # Refresh Token (7일)
        refresh_payload = {
            "sub": user_id,
            "exp": now + timedelta(days=7),
            "iat": now
        }
        refresh_token = jwt.encode(refresh_payload, REFRESH_SECRET, algorithm="HS256")

        return access_token, refresh_token

    return _create_tokens


# Audio 테스트용 fixtures
@pytest.fixture
def sample_audio_bytes():
    '''
    테스트용 샘플 오디오 바이트 데이터

    실제 오디오는 아니지만 크기 검증용으로 충분함
    '''
    return b"fake_audio_data" * 100  # 1500 bytes
