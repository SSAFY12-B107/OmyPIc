# FastAPI 소셜 로그인 & JWT 인증 구현

이 프로젝트는 FastAPI 프레임워크를 사용하여 카카오 소셜 로그인과 JWT 인증을 구현한 예제입니다. Redis를 사용한 토큰 인증 시스템을 포함하고 있으며, 향후 구글 소셜 로그인 추가에 대비한 구조를 갖추고 있습니다.

## 주요 기능

- 카카오 소셜 로그인 구현
- JWT 인증 방식 (Redis DB 활용)
- fastapi-users 라이브러리 활용
- 확장 가능한 구조 (구글 소셜 로그인 추가 가능)
- 사용자 프로필 관리 (오픽 관련 정보 포함)

## 사용자 모델 필드

- 유저 이메일: 소셜 로그인을 통해 제공된 이메일 (중복 허용, 다른 소셜 계정과 연동 가능)
- 유저 이름: 소셜 로그인을 통해 제공된 이름
- 유저의 현재 오픽 성적 (nullable=True)
- 유저의 희망 오픽 성적 (nullable=True) - 온보딩 설문에서 수집
- 유저의 희망 시험 일자 (nullable=True) - 온보딩 설문에서 수집
- 유저의 예상 오픽 성적 (nullable=True) - 온보딩 설문에서 수집
- 온보딩 완료 여부 (is_onboarded): 사용자가 초기 설문을 완료했는지 여부저 이름: 소셜 로그인을 통해 제공된 이름
- 유저의 현재 오픽 성적 (nullable=True)
- 유저의 희망 오픽 성적
- 유저의 희망 시험 일자 (nullable=True)
- 유저의 예상 오픽 성적

## 설치 방법

1. 필요한 패키지 설치:

```bash
pip install fastapi uvicorn sqlalchemy fastapi-users[sqlalchemy] python-jose[cryptography] redis httpx
```

2. Redis 서버 설치 및 실행:

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo service redis-server start

# macOS (Homebrew)
brew install redis
brew services start redis

# Windows: Redis 공식 사이트에서 Redis for Windows 다운로드
```

3. 환경 변수 설정:

```bash
# .env 파일 생성
SECRET_KEY=your-secret-key
KAKAO_CLIENT_ID=your-kakao-client-id
KAKAO_CLIENT_SECRET=your-kakao-client-secret
KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

## 카카오 개발자 설정

1. [카카오 개발자 센터](https://developers.kakao.com)에서 애플리케이션 등록
2. 카카오 로그인 활성화
3. 동의항목 설정: 필수 (닉네임, 이메일)
4. 플랫폼 등록: 웹 플랫폼, 로컬 도메인 (http://localhost:8000)
5. Redirect URI 설정: http://localhost:8000/auth/kakao/callback

## 실행 방법

```bash
uvicorn main:app --reload
```

## API 엔드포인트

- `GET /`: API 루트 엔드포인트
- `GET /auth/kakao/login`: 카카오 로그인 시작
- `GET /auth/kakao/callback`: 카카오 로그인 콜백 처리 (액세스 토큰과 리프레시 토큰 발급)
- `GET /users/me`: 현재 로그인한 사용자 정보 조회
- `PATCH /users/me`: 사용자 정보 업데이트
- `POST /users/onboarding`: 사용자 초기 설문 정보 저장 (목표 오픽 성적, 예상 오픽 성적 등)
- `POST /auth/jwt/login`: JWT 액세스 토큰 로그인 (일반 로그인용, 소셜 로그인에서는 사용하지 않음)
- `POST /auth/refresh`: 리프레시 토큰을 사용한 액세스 토큰 및 리프레시 토큰 재발급

## 구조 설명

1. **데이터베이스 모델**:
   - `UserModel`: 사용자 정보 저장
   - `SocialAccount`: 소셜 계정 정보 저장 (여러 소셜 계정을 하나의 사용자에 연결 가능)

2. **인증 시스템**:
   - 액세스 토큰: JWT 기반, 짧은 수명(30분), 세션 스토리지에 저장
   - 리프레시 토큰: Redis 기반, 긴 수명(7일), HTTP 전용 쿠키에 저장
   - fastapi-users를 활용한 인증 미들웨어

3. **소셜 로그인 흐름**:
   - 소셜 로그인 요청 → 소셜 서비스 인증 → 콜백 처리 → 사용자 생성/조회 → 액세스 토큰 및 리프레시 토큰 발급
   - 신규 사용자의 경우 온보딩 페이지로 리다이렉트하여 초기 설문 수집

4. **온보딩 흐름**:
   - 소셜 로그인 후 사용자가 온보딩 페이지로 리다이렉트됨
   - 사용자가 오픽 관련 정보(목표 성적, 예상 성적 등) 입력
   - `/users/onboarding` 엔드포인트를 통해 정보 저장 및 `is_onboarded` 플래그 업데이트

5. **토큰 갱신 흐름**:
   - 액세스 토큰 만료 → 리프레시 토큰으로 `/auth/refresh` 엔드포인트 호출 → 새 액세스 토큰 및 리프레시 토큰 발급

## 구글 소셜 로그인 추가 방법

이 프로젝트는 구글 소셜 로그인을 추가할 수 있는 구조로 설계되어 있습니다. 구글 소셜 로그인을 추가하려면:

1. 구글 개발자 콘솔에서 OAuth 2.0 클라이언트 ID 생성
2. `auth/google/login` 및 `auth/google/callback` 엔드포인트 구현
3. 기존 `UserManager.create_social_user()` 메서드 활용

## 문제 해결

- **Redis 연결 오류**: Redis 서버가 실행 중인지 확인하고 `REDIS_URL` 설정을 확인하세요.
- **카카오 로그인 실패**: 카카오 개발자 콘솔에서 Redirect URI와 동의항목 설정을 확인하세요.
- **JWT 토큰 문제**: `SECRET_KEY`가 올바르게 설정되었는지 확인하세요.

## 보안 고려사항

- 실제 프로덕션 환경에서는 `SECRET_KEY`와 같은 중요한 정보를 환경 변수로 관리하세요.
- HTTPS를 사용하여 통신을 암호화하세요.
- 소셜 로그인 클라이언트 ID와 시크릿 키를 안전하게 보관하세요.