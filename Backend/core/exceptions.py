"""
커스텀 예외 클래스 모듈
Celery 작업에서 사용하는 도메인 특화 예외들을 정의
"""


class APIQuotaExceededError(Exception):
    """
    API 할당량 초과 오류

    OpenAI API 등 외부 API의 할당량(quota)이 초과되었을 때 발생
    이 예외가 발생하면 Celery auto-retry가 지수 백오프로 재시도
    """
    pass


class APIRateLimitError(Exception):
    """
    API Rate Limit 오류

    API의 요청 빈도 제한(rate limit)에 도달했을 때 발생
    429 상태 코드나 "rate limit" 메시지를 감지하여 발생
    """
    pass


class EvaluationError(Exception):
    """
    평가 처리 중 오류

    ResponseEvaluator의 평가 과정에서 발생하는 일반적인 오류
    API 할당량이나 Rate Limit이 아닌 기타 평가 오류
    """
    pass
