FROM python:3.11-slim

WORKDIR /app

# 필요한 시스템 패키지 설치 (Git, ffmpeg, Python 개발 패키지, ALSA 포함)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    python3-dev \
    libasound2-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 종속성 파일 복사 (캐싱을 위해 먼저 복사)
COPY requirements.txt .

# pip 업그레이드 후 의존성 설치 (안정성 향상을 위해)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 실행 설정
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]