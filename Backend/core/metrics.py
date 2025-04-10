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


def normalize_label_value(value: str) -> str:
    """
    Prometheus label로 사용할 수 있도록 정규화된 문자열 반환
    - 알파벳, 숫자, 하이픈, 언더스코어만 허용
    - 공백은 _로 대체, 대문자는 소문자로 변환
    """
    import re
    value = value.strip().lower().replace(" ", "_")
    return re.sub(r'[^a-z0-9_\-]', '_', value)

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
                labels = {k: normalize_label_value(str(v)) for k, v in labels_dict.items()}
                labels["status"] = normalize_label_value(status)
                try:
                    metric.labels(**labels).observe(duration)
                except Exception as label_error:
                    import logging
                    logging.getLogger(__name__).error(f"메트릭 레이블 오류: {label_error}, 레이블: {labels}")

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
                
                # track_time_async 함수 수정 부분
                safe_labels = {}
                for k, v in labels.items():
                    if k in metric._labelnames:
                        # 모든 레이블 값 정규화
                        safe_labels[k] = normalize_label_value(str(v))

                try:
                    metric.labels(**safe_labels).observe(duration)
                except Exception as label_error:
                    import logging
                    logging.getLogger(__name__).error(f"메트릭 레이블 오류: {label_error}, 레이블: {safe_labels}")
                
                # 활성 작업 감소 (해당되는 경우)
                if "task_type" in labels_dict and "task_type" in [label for label in ACTIVE_TASKS._labelnames]:
                    ACTIVE_TASKS.labels(task_type=labels_dict["task_type"]).dec()
        
        return wrapper
    return decorator

def track_audio_processing(processor="standard"):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                return await func(*args, **kwargs)
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                AUDIO_PROCESS_DURATION.labels(status=status, processor=processor).observe(duration)
        return wrapper
    return decorator

# 오디오 처리 시간 기록 데코레이터
# def track_audio_processing_time(func):
#     async def wrapper(*args, **kwargs):
#         start_time = time.time()
#         status = "success"
        
#         try:
#             result = await func(*args, **kwargs)
#             return result
#         except Exception as e:
#             status = "error"
#             raise
#         finally:
#             duration = time.time() - start_time
#             AUDIO_PROCESS_DURATION.labels(status=status, processor="standard").observe(duration)
    
#     return wrapper

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
            labels = {
                "provider": normalize_label_value(provider),
                "model": normalize_label_value(model),
                "operation": "default",
                "status": normalize_label_value(status)
            }
            try:
                LLM_API_DURATION.labels(**labels).observe(duration)
            except Exception as label_error:
                import logging
                logging.getLogger(__name__).error(f"메트릭 레이블 오류: {label_error}, 레이블: {labels}")
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
    try:
        # 카테고리 정규화
        safe_category = normalize_category(problem_category)
        PROBLEM_TYPE_EVALUATION_TIME.labels(problem_category=safe_category, status=status).observe(duration)
    except Exception as e:
        # 메트릭 기록 실패 시 로그만 남기고 계속 진행
        import logging
        logging.getLogger(__name__).error(f"메트릭 기록 중 오류: {str(e)}")


def normalize_category(category: str) -> str:
    """카테고리 이름을 프로메테우스 레이블로 사용 가능하게 정규화"""
    if not category:
        return "unknown"
        
    # 지원하는 카테고리 매핑
    mapping = {
        "과거 경험": "past_experience",
        "과거경험": "past_experience",
        "묘사": "description",
        "롤플레이": "roleplay",
        "롤플레잉": "roleplay",
        "자기소개": "self_introduction",
        "비교": "comparison",
        "루틴": "routine",
        "기술": "technology",
        "영화보기": "watching_movies"
    }
    
    # 매핑된 값이 있으면 반환
    if category in mapping:
        return mapping[category]
    
    # 없으면 영문자/숫자/언더스코어만 남기고 나머지는 _로 대체
    import re
    normalized = re.sub(r'[^a-zA-Z0-9_]', '_', category.lower())
    
    # 빈 문자열이 되면 unknown 반환
    return normalized if normalized else "unknown"


# 레이블 값 정규화 함수 추가
def normalize_label_value(value: str) -> str:
    """프로메테우스 레이블 값 정규화"""
    if not value:
        return "unknown"
    
    # 하이픈을 언더스코어로 변환하고 나머지는 영문자/숫자/언더스코어만 유지
    import re
    normalized = re.sub(r'[^a-zA-Z0-9_]', '_', str(value))
    return normalized if normalized else "unknown"