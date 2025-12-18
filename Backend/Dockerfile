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

# ============================================================================
# Celery Worker 실행 명령어 (참고용 - 별도 컨테이너에서 실행)
# ============================================================================
#
# Gevent ㅇ 사용 Celery Worker 실행:
# celery -A celery_worker.celery_app worker \
#   --pool=gevent \
#   --concurrency=100 \
#   --loglevel=info \
#   --max-tasks-per-child=500 \
#   --max-memory-per-child=512000
#
# 또는 celery_worker.py의 설정을 사용하는 경우:
# celery -A celery_worker.celery_app worker --loglevel=info
# (worker_pool, worker_concurrency 등은 celery_worker.py에 설정되어 있음)
#
# Flower 모니터링 대시보드 실행 (선택사항):
# celery -A celery_worker.celery_app flower --port=5555
# ============================================================================