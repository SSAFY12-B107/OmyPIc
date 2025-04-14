from celery import Celery
from core.config import settings

from prometheus_client import make_asgi_app
# from fastapi import FastAPI

metrics_app = make_asgi_app()

# app = FastAPI()
# app.mount("/metrics", metrics_app)

# Redis URL 설정
redis_url = settings.REDIS_URL if hasattr(settings, 'REDIS_URL') else 'redis://localhost:6379/0'
# redis_url = "redis://127.0.0.1:6379/0"  # localhost 대신 IP 주소 사용


print(settings.REDIS_URL)

# Celery 앱 초기화
celery_app = Celery(
    'omypic_worker',
    broker=redis_url,
    backend=redis_url,
    broker_transport_options={'visibility_timeout': 3600},
    include=['tasks.audio_tasks']
)

# Celery 설정
celery_app.conf.update(
    broker_transport='redis',
    result_backend_transport='redis',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=False,
    worker_max_tasks_per_child=100,  # 메모리 누수 방지
    task_track_started=True,
    task_time_limit=1800,  # 30분 제한 (오디오 처리 시간 고려)
    result_expires=60 * 60 * 24  # 1일 후 결과 만료
)

if __name__ == '__main__':
    celery_app.start()

