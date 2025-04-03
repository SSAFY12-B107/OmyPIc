# core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import functools

# 종합 측정 항목 정의
REQUEST_COUNT = Counter(
    "http_requests_total", 
    "전체 HTTP 요청 수",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", 
    "HTTP 요청 처리 시간(초)",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float("inf"))
)

REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "현재 처리 중인 HTTP 요청 수",
    ["method", "endpoint"]
)

# API 서비스 전용 측정 항목
AUDIO_PROCESS_DURATION = Histogram(
    "audio_process_duration_seconds", 
    "오디오 처리 시간(초)",
    ["status", "processor"],
    buckets=(0.5, 1, 2.5, 5, 10, 30, 60, 120, 300, float("inf"))
)

LLM_API_DURATION = Histogram(
    "llm_api_duration_seconds", 
    "LLM API 호출 시간(초)",
    ["provider", "model", "operation", "status"],
    buckets=(0.5, 1, 2.5, 5, 10, 30, 60, 120, 300, float("inf"))
)

# 추가 측정 항목
BACKGROUND_TASK_DURATION = Histogram(
    "background_task_duration_seconds", 
    "배경 작업 처리 시간(초)",
    ["task_type", "status"],
    buckets=(0.1, 0.5, 1, 3, 5, 10, 30, 60, 300, 600, 1800)
)

ACTIVE_TASKS = Gauge(
    "active_tasks",
    "현재 실행 중인 작업 수",
    ["task_type"]
)

ERROR_COUNTER = Counter(
    "error_count_total", 
    "처리 중 발생한 오류 수",
    ["module", "error_type"]
)

# 음성 파일 크기별 처리 시간 상관 관계
AUDIO_SIZE_VS_PROCESS_TIME = Summary(
    "audio_size_vs_process_time_seconds", 
    "오디오 크기(MB)별 처리 시간(초)",
    ["processor"]
)

# 문제 유형별 평가 시간 측정
PROBLEM_TYPE_EVALUATION_TIME = Histogram(
    "problem_type_evaluation_time_seconds",
    "문제 유형별 평가 시간(초)",
    ["problem_category", "status"],
    buckets=(0.5, 1, 2.5, 5, 10, 30, 60, 120, 300)
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 경로 정규화 (파라미터 제거)
        endpoint = request.url.path
        for param in request.path_params:
            endpoint = endpoint.replace(request.path_params[param], f"{{{param}}}")
        
        method = request.method
        
        # 진행 중인 요청 카운터 증가
        REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
        
        # 요청 시간 측정 시작
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # 처리 시간 계산
            duration = time.time() - start_time
            status_code = response.status_code
            
            # 측정 항목 업데이트
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            
            return response
        except Exception as exc:
            # 오류 발생 시에도 측정 항목 업데이트
            duration = time.time() - start_time
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=500).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            
            # 오류 유형 기록
            error_type = type(exc).__name__
            ERROR_COUNTER.labels(module="http_middleware", error_type=error_type).inc()
            
            raise exc
        finally:
            # 요청 처리 완료 시 진행 중인 요청 카운터 감소
            REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()

# 연속적인 측정 지표 기록을 위한 데코레이터 (동기 함수용)
def track_time(metric, labels_dict):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                # 오류 유형에 따라 오류 카운터 증가
                error_type = type(e).__name__
                ERROR_COUNTER.labels(module=func.__module__, error_type=error_type).inc()
                raise
            finally:
                duration = time.time() - start_time
                # 라벨 사전에 상태 추가
                labels = {**labels_dict, "status": status}
                metric.labels(**labels).observe(duration)
        
        return wrapper
    return decorator

# 비동기 함수용 측정 데코레이터
def track_time_async(metric, labels_dict):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            # 활성 작업 증가 (해당되는 경우)
            if "task_type" in labels_dict and "task_type" in [label for label in ACTIVE_TASKS._labelnames]:
                ACTIVE_TASKS.labels(task_type=labels_dict["task_type"]).inc()
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                # 오류 유형에 따라 오류 카운터 증가
                error_type = type(e).__name__
                ERROR_COUNTER.labels(module=func.__module__, error_type=error_type).inc()
                raise
            finally:
                duration = time.time() - start_time
                # 라벨 사전에 상태 추가
                labels = {**labels_dict, "status": status}
                
                # 라벨이 메트릭의 라벨네임과 일치하는지 확인
                valid_labels = {k: v for k, v in labels.items() if k in metric._labelnames}
                metric.labels(**valid_labels).observe(duration)
                
                # 활성 작업 감소 (해당되는 경우)
                if "task_type" in labels_dict and "task_type" in [label for label in ACTIVE_TASKS._labelnames]:
                    ACTIVE_TASKS.labels(task_type=labels_dict["task_type"]).dec()
        
        return wrapper
    return decorator

# 오디오 처리 시간 기록 데코레이터
def track_audio_processing_time(func):
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        status = "success"
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status = "error"
            raise
        finally:
            duration = time.time() - start_time
            AUDIO_PROCESS_DURATION.labels(status=status, processor="standard").observe(duration)
    
    return wrapper

# LLM API 호출 시간 기록 함수
def track_llm_api_call(provider, model, func):
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        status = "success"
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status = "error"
            raise
        finally:
            duration = time.time() - start_time
            LLM_API_DURATION.labels(provider=provider, model=model, operation="default", status=status).observe(duration)
    
    return wrapper

# 오디오 파일 크기 추적 헬퍼 함수
def track_audio_size(audio_content: bytes, processor: str = "standard"):
    """오디오 파일 크기를 MB 단위로 기록"""
    file_size_mb = len(audio_content) / (1024 * 1024)
    AUDIO_SIZE_VS_PROCESS_TIME.labels(processor=processor).observe(file_size_mb)
    return file_size_mb

# 문제 유형별 평가 시간 기록 함수
def track_problem_evaluation_time(problem_category: str, duration: float, status: str = "success"):
    """문제 유형별 평가 시간 기록"""
    PROBLEM_TYPE_EVALUATION_TIME.labels(problem_category=problem_category, status=status).observe(duration)