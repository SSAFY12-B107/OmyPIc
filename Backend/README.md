# 🛠️ Backend Project

이 프로젝트는 FastAPI 기반의 백엔드 서비스입니다.  
Docker 환경에서 손쉽게 실행 가능하며, 구조화된 폴더 구성을 통해 유지보수가 용이하도록 설계되었습니다.

---

## 📁 프로젝트 구조 *

```
📁 Backend/
├── 📁 api/              # 라우터 및 엔드포인트 정의
├── 📁 core/             # 설정, 환경변수, 보안 등 핵심 설정
├── 📁 db/               # 데이터베이스 초기화 및 세션 관리
├── 📁 models/           # SQLAlchemy ORM 모델 정의
├── 📁 schemas/          # Pydantic 기반 데이터 유효성 및 직렬화
├── 📁 scripts/          # 초기화 스크립트 및 유틸리티
├── 📁 services/         # 비즈니스 로직 구현
├── 📁 tests/            # 테스트 코드
├── 📁 venv/             # 가상 환경 (보통 Git에 포함하지 않음)
├── __init__.py         # 패키지 초기화 파일
├── .env                # 환경 변수 파일
├── .env.example        # 예시 환경 변수 파일
├── .gitignore          # Git 추적 제외 파일 목록
├── docker-compose.yml  # 도커 컴포즈 설정
├── Dockerfile          # 도커 이미지 빌드 설정
├── main.py             # 애플리케이션 진입점 (FastAPI 실행)
├── README.md           # 프로젝트 설명 문서
└── requirements.txt    # 의존성 패키지 목록
```

---

## ▶️ 실행 방법 (로컬 환경)

1. 가상 환경 생성 및 활성화
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

2. 의존성 설치
    ```bash
    pip install -r requirements.txt
    ```

### ✅ `pip install -r requirements.txt` 인코딩 관련 안내

- `requirements.txt`에 **한글 주석**이 포함되어 있을 경우, **파일을 반드시 UTF-8 인코딩으로 저장**해야 합니다.
- 그렇지 않으면 `UnicodeDecodeError: 'cp949' codec can't decode byte...` 와 같은 에러가 발생할 수 있습니다.

---

### 📦 설치 명령어

```bash
pip install -r requirements.txt --no-cache-dir
```

- 위 명령어로 설치할 때 인코딩 관련 에러가 발생하면,  
  **`requirements.txt` 파일이 메모장 또는 VSCode에서 UTF-8로 저장되었는지 꼭 확인해주세요!**


3. 환경 변수 파일 생성
    ```bash
    cp .env.example .env
    ```

4. 서버 실행
    ```bash
    uvicorn main:app --reload
    ```

---

## ⚙️ 환경 변수 (.env)

| 변수명                         | 설명                                      | 예시 또는 형식                            |
|-------------------------------|-------------------------------------------|-------------------------------------------|
| `JWT_SECRET_KEY`              | 액세스 토큰 서명을 위한 비밀 키           | `your-jwt-secret-key`                     |
| `REFRESH_TOKEN_SECRET_KEY`    | 리프레시 토큰 서명을 위한 비밀 키         | `your-refresh-secret-key`                 |
| `JWT_ALGORITHM`               | JWT 알고리즘                              | `HS256`                                   |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 액세스 토큰 만료 시간 (분)                | `30`                                      |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | 리프레시 토큰 만료 시간 (일)              | `7`                                       |
| `MONGODB_URL`                 | MongoDB 접속 URI                          | `mongodb+srv://user:pass@cluster.mongodb.net` |
| `MONGODB_DB_NAME`            | 사용할 MongoDB 데이터베이스 이름          | `mydatabase`                               |
| `CORS_ORIGINS`               | 허용할 CORS 오리진 (쉼표로 구분)          | `http://localhost:3000,http://example.com` |
| `FRONTEND_URL`               | 프론트엔드 서비스 주소                    | `http://localhost:3000`                    |
| `NAVER_CLIENT_ID`            | 네이버 OAuth Client ID                    | `your-naver-client-id`                     |
| `NAVER_CLIENT_SECRET`        | 네이버 OAuth Client Secret                | `your-naver-client-secret`                 |
| `NAVER_REDIRECT_URI`         | 네이버 OAuth Redirect URI                 | `http://localhost:8000/auth/naver/callback`|
| `GOOGLE_CLIENT_ID`           | Google OAuth Client ID                    | `your-google-client-id`                    |
| `GOOGLE_CLIENT_SECRET`       | Google OAuth Client Secret                | `your-google-client-secret`                |
| `GOOGLE_REDIRECT_URI`        | Google OAuth Redirect URI                 | `http://localhost:8000/auth/google/callback`|
| `AWS_ACCESS_KEY_ID`          | AWS 액세스 키                             | `your-aws-access-key-id`                   |
| `AWS_SECRET_ACCESS_KEY`      | AWS 시크릿 키                             | `your-aws-secret-access-key`               |
| `AWS_REGION`                 | S3 버킷이 위치한 AWS 리전                 | `ap-northeast-2`                           |
| `AWS_S3_BUCKET_NAME`         | 사용할 S3 버킷 이름                       | `your-bucket-name`                         |
| `GEMINI_API_KEYS`            | Google Gemini API 키 (쉼표로 다중 입력 가능) | `key1,key2`                             |
| `GROQ_API_KEYS`              | Groq API 키 (쉼표로 다중 입력 가능)         | `key1,key2`                             |


`.env.example` 참고 후 `.env` 파일 생성 필요

---

## 🐳 Docker로 실행

1. `.env` 파일 확인
2. 아래 명령어 실행
    ```bash
    docker-compose up --build
    ```

3. 브라우저에서 접속
    ```
    http://localhost:8000
    ```

---

## 🧪 테스트

```bash
pytest tests/
```

---

## 📌 기타

- 문서 확인: `http://localhost:8000/docs` (Swagger UI)
- OpenAPI JSON: `http://localhost:8000/openapi.json`
test 2
---



