"""
OmyPIC STT/LLM 메트릭 생성 시뮬레이션 스크립트

이 스크립트는 실제 API 호출 없이 Prometheus 메트릭을 시뮬레이션하여 생성합니다.
Grafana 대시보드 동작 확인용입니다.

실행 방법:
  docker exec -it omypic-fastapi python /app/tests/generate_metrics.py

또는 로컬에서:
  cd Backend
  python tests/generate_metrics.py
"""

import sys
import os
import time
import random
import logging

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def simulate_metrics():
    """실제 API 호출 없이 Prometheus 메트릭 시뮬레이션"""

    # Prometheus 메트릭 임포트
    from core.metrics import (
        AUDIO_PROCESS_DURATION,
        LLM_API_DURATION,
        BACKGROUND_TASK_DURATION,
        ACTIVE_TASKS,
        PROBLEM_TYPE_EVALUATION_TIME,
        ERROR_COUNTER,
        normalize_label_value
    )

    logger.info("="*70)
    logger.info("OmyPIC 메트릭 시뮬레이션 시작")
    logger.info("="*70)

    # 테스트 시나리오 정의
    scenarios = [
        {"category": "past_experience", "stt_time": 3.5, "llm_time": 5.2},
        {"category": "description", "stt_time": 2.8, "llm_time": 4.8},
        {"category": "roleplay", "stt_time": 4.2, "llm_time": 6.1},
        {"category": "self_introduction", "stt_time": 2.5, "llm_time": 4.0},
        {"category": "comparison", "stt_time": 3.8, "llm_time": 5.5},
        {"category": "routine", "stt_time": 3.0, "llm_time": 4.5},
        {"category": "technology", "stt_time": 3.3, "llm_time": 5.8},
        {"category": "watching_movies", "stt_time": 2.9, "llm_time": 4.3},
    ]

    total_tests = 20  # 총 테스트 수

    for i in range(total_tests):
        scenario = random.choice(scenarios)
        category = scenario["category"]

        # 랜덤 변동 추가 (±30%)
        stt_time = scenario["stt_time"] * random.uniform(0.7, 1.3)
        llm_time = scenario["llm_time"] * random.uniform(0.7, 1.3)
        task_time = stt_time + llm_time + random.uniform(0.5, 2.0)

        logger.info(f"\n[{i+1}/{total_tests}] 시뮬레이션 - 카테고리: {category}")

        # 1. STT 메트릭 기록
        AUDIO_PROCESS_DURATION.labels(
            status="success",
            processor="wit_ai"
        ).observe(stt_time)
        logger.info(f"  🎤 STT 처리 시간: {stt_time:.2f}초")

        # 2. LLM 메트릭 기록
        LLM_API_DURATION.labels(
            provider="google",
            model="gemini_1_5_pro",
            operation="evaluate_response",
            status="success"
        ).observe(llm_time)
        logger.info(f"  🤖 LLM 응답 시간: {llm_time:.2f}초")

        # 3. Background Task 메트릭 기록
        BACKGROUND_TASK_DURATION.labels(
            task_type="audio_evaluation",
            status="success"
        ).observe(task_time)
        logger.info(f"  ⚙️ 작업 처리 시간: {task_time:.2f}초")

        # 4. 문제 유형별 평가 시간 기록
        PROBLEM_TYPE_EVALUATION_TIME.labels(
            problem_category=category,
            status="success"
        ).observe(llm_time)
        logger.info(f"  📝 문제 유형: {category}")

        # 5. 활성 작업 시뮬레이션 (증가 후 감소)
        ACTIVE_TASKS.labels(task_type="audio_evaluation").inc()
        time.sleep(0.1)  # 짧은 대기
        ACTIVE_TASKS.labels(task_type="audio_evaluation").dec()

        # 6. 간헐적 에러 시뮬레이션 (10% 확률)
        if random.random() < 0.1:
            error_type = random.choice(["TimeoutError", "APIError", "ValidationError"])
            ERROR_COUNTER.labels(
                module="audio_processor" if random.random() < 0.5 else "evaluator",
                error_type=error_type
            ).inc()
            logger.info(f"  ⚠️ 에러 시뮬레이션: {error_type}")

        # 다음 테스트까지 짧은 대기
        time.sleep(0.3)

    # 추가: 다양한 처리 시간 분포를 위한 추가 메트릭
    logger.info("\n" + "="*70)
    logger.info("추가 메트릭 생성 중...")

    # 빠른 요청들
    for _ in range(10):
        AUDIO_PROCESS_DURATION.labels(status="success", processor="wit_ai").observe(random.uniform(1.0, 2.5))
        LLM_API_DURATION.labels(provider="google", model="gemini_1_5_pro", operation="evaluate_response", status="success").observe(random.uniform(2.0, 4.0))

    # 느린 요청들
    for _ in range(5):
        AUDIO_PROCESS_DURATION.labels(status="success", processor="wit_ai").observe(random.uniform(5.0, 10.0))
        LLM_API_DURATION.labels(provider="google", model="gemini_1_5_pro", operation="evaluate_response", status="success").observe(random.uniform(8.0, 15.0))

    # 결과 요약
    logger.info("\n" + "="*70)
    logger.info("메트릭 시뮬레이션 완료!")
    logger.info("="*70)
    logger.info(f"총 {total_tests + 15}개의 메트릭 포인트 생성됨")
    logger.info("\nGrafana에서 확인:")
    logger.info("  - URL: http://localhost:3001")
    logger.info("  - 계정: admin / omypic123")
    logger.info("  - 대시보드: OmyPIC Backend Monitoring")
    logger.info("="*70)


if __name__ == "__main__":
    simulate_metrics()
