from celery import Celery
from core.config import settings

# Redis URL 설정
redis_url = settings.REDIS_URL if hasattr(settings, 'REDIS_URL') else 'redis://localhost:6379/0'

print(f"Redis URL: {redis_url}")

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
    # 기본 설정
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=False,
    result_expires=60 * 60 * 24,  # 1일 후 결과 만료
    task_track_started=True,

    # Worker Pool 설정 - Gevent를 사용한 I/O Bound 작업 최적화
    # Gevent: 경량 코루틴 기반으로 외부 API 호출 등 I/O 대기 시간에 다른 작업 처리 가능
    worker_pool='gevent',  # I/O Bound 작업에 최적화된 gevent pool 사용
    worker_concurrency=100,  # 동시 처리 가능한 작업 수: 4개 → 100개로 대폭 증가

    # Worker 리소스 관리
    # 메모리 누수 방지를 위해 일정 작업 수 또는 메모리 사용량 초과 시 워커 재시작
    worker_max_tasks_per_child=500,  # 워커당 최대 500개 작업 처리 후 재시작 (메모리 누수 방지)
    worker_max_memory_per_child=512000,  # 워커당 최대 512MB 메모리 사용 시 재시작

    # Task 실행 시간 제한
    task_time_limit=1800,  # 30분 하드 리미트 (강제 종료)
    task_soft_time_limit=1500,  # 25분 소프트 리미트 (SoftTimeLimitExceeded 예외 발생, 정리 작업 가능)

    # Task 재시도 설정
    task_default_retry_delay=60,  # 실패 시 60초 후 재시도

    # Task별 재시도 정책 (annotations)
    task_annotations={
        'tasks.audio_tasks.*': {
            'rate_limit': '10/m',  # 분당 최대 10개 작업 처리 (API 제한 고려)
            'max_retries': 3,  # 최대 3번 재시도
            'retry_backoff': True,  # 지수 백오프 재시도 (1분 → 2분 → 4분)
            'retry_backoff_max': 600,  # 최대 10분까지 백오프
            'retry_jitter': True,  # 재시도 시간에 랜덤 지터 추가 (동시 재시도 방지)
        }
    }
)

if __name__ == '__main__':
    celery_app.start()

