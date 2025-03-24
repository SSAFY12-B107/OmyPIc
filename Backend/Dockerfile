FROM python:3.12-slim

WORKDIR /app

# 종속성 파일 복사 (캐싱을 위해 먼저 복사)
COPY requirements.txt .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 실행 설정
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]