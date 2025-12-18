# OmyPIC Backend 모니터링 스택

> 작성일: 2025-12-18
> 목적: FastAPI, Celery, Redis 성능 및 안정성 실시간 모니터링

## 개요

OmyPIC Backend 프로젝트의 종합 모니터링 솔루션입니다. Prometheus를 활용한 메트릭 수집과 Grafana를 통한 시각화로 시스템 상태를 실시간으로 파악할 수 있습니다.

## 구성 요소

### 1. Prometheus (메트릭 수집 및 저장)
- **포트**: 9090
- **역할**: 시계열 데이터베이스, Pull 기반 메트릭 수집
- **수집 대상**:
  - FastAPI 애플리케이션 (`/metrics` 엔드포인트)
  - Redis (Redis Exporter를 통해)
  - Celery (Flower를 통해)

### 2. Grafana (데이터 시각화)
- **포트**: 3001
- **역할**: 대시보드, 알림, 데이터 분석
- **기본 계정**: `admin / omypic123`
- **기능**:
  - 실시간 성능 모니터링
  - 문제 유형별 평가 시간 추적
  - LLM API 호출 시간 분석

### 3. Redis Exporter (Redis 메트릭)
- **포트**: 9121
- **역할**: Redis 상태를 Prometheus 형식으로 변환
- **수집 메트릭**:
  - 메모리 사용량
  - 연결 수
  - 키 개수
  - 캐시 히트율

### 4. Celery Flower (작업 모니터링)
- **포트**: 5555
- **역할**: Celery 워커 및 작업 큐 모니터링
- **기능**:
  - 실시간 작업 추적
  - 워커 상태 확인
  - 재시도 로그

## 시작하기

### 1. 환경 변수 설정

`.env` 파일에 Redis 연결 정보가 있는지 확인:

```bash
REDIS_URL=redis://localhost:6379/0
```

### 2. 모니터링 스택 실행

```bash
# 모니터링 서비스 시작
docker-compose -f docker-compose.monitoring.yml up -d

# 로그 확인
docker-compose -f docker-compose.monitoring.yml logs -f

# 특정 서비스 로그만 확인
docker-compose -f docker-compose.monitoring.yml logs -f prometheus
docker-compose -f docker-compose.monitoring.yml logs -f grafana
```

### 3. 서비스 접근

| 서비스 | URL | 계정 |
|--------|-----|------|
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3001 | admin / omypic123 |
| Flower | http://localhost:5555 | - |
| Redis Exporter | http://localhost:9121/metrics | - |

### 4. FastAPI 애플리케이션 실행

모니터링 스택이 메트릭을 수집하려면 FastAPI 애플리케이션이 실행 중이어야 합니다:

```bash
# 로컬 실행
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 또는 Docker로 실행
docker-compose up -d
```

### 5. Celery 워커 실행

Celery 메트릭을 수집하려면 워커가 실행 중이어야 합니다:

```bash
# Gevent Pool 사용
celery -A celery_worker.celery_app worker --pool=gevent --concurrency=100 --loglevel=info
```

## 대시보드 구성

### 시스템 개요 패널
- **총 요청 속도**: 초당 요청 수 (req/s)
- **응답 시간**: 95th percentile
- **진행 중인 요청 수**: 동시 처리 중인 요청
- **에러 발생률**: 초당 에러 수

### HTTP 요청 분석
- **엔드포인트별 요청 속도**: API 엔드포인트별 트래픽 분포
- **응답 시간 Percentiles**: p50, p95, p99 지연 시간

### Celery 작업 모니터링
- **활성 작업 수**: 작업 유형별 진행 중인 작업
- **작업 처리 시간**: 작업 유형별 처리 시간

### 비즈니스 메트릭
- **오디오 처리 시간**: STT 처리 성능
- **LLM API 호출 시간**: Gemini/Groq API 응답 시간
- **문제 유형별 평가 시간**: 카테고리별 평가 성능

### Redis 모니터링
- **메모리 사용량**: 현재/최대 메모리
- **연결 수**: 활성 클라이언트 연결

## 메트릭 수집 구조

### FastAPI 메트릭 (`core/metrics.py`)

```python
# HTTP 메트릭
REQUEST_COUNT = Counter("http_requests_total", ...)
REQUEST_LATENCY = Histogram("http_request_duration_seconds", ...)
REQUESTS_IN_PROGRESS = Gauge("http_requests_in_progress", ...)

# 비즈니스 메트릭
AUDIO_PROCESS_DURATION = Histogram("audio_process_duration_seconds", ...)
LLM_API_DURATION = Histogram("llm_api_duration_seconds", ...)
PROBLEM_TYPE_EVALUATION_TIME = Histogram("problem_type_evaluation_time_seconds", ...)

# Celery 메트릭
BACKGROUND_TASK_DURATION = Histogram("background_task_duration_seconds", ...)
ACTIVE_TASKS = Gauge("active_tasks", ...)
ERROR_COUNTER = Counter("error_count_total", ...)
```

### Prometheus 수집 설정 (`prometheus.yml`)

```yaml
scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis_exporter:9121']
    scrape_interval: 15s

  - job_name: 'celery'
    static_configs:
      - targets: ['flower:5555']
    scrape_interval: 15s
```

## 문제 해결

### Prometheus에서 타겟이 DOWN으로 표시될 때

1. **FastAPI 타겟이 DOWN**:
   ```bash
   # FastAPI 애플리케이션이 실행 중인지 확인
   curl http://localhost:8000/metrics

   # Docker 네트워크 확인
   docker network inspect omypic_network
   ```

2. **Redis Exporter가 DOWN**:
   ```bash
   # Redis 연결 확인
   docker-compose -f docker-compose.monitoring.yml logs redis_exporter

   # Redis 서버 상태 확인
   redis-cli ping
   ```

3. **Flower가 DOWN**:
   ```bash
   # Celery 워커 실행 확인
   celery -A celery_worker.celery_app inspect active

   # Flower 로그 확인
   docker-compose -f docker-compose.monitoring.yml logs flower
   ```

### Grafana에서 "No data" 표시될 때

1. **데이터소스 연결 확인**:
   - Grafana UI → Configuration → Data Sources
   - Prometheus 데이터소스 "Test" 버튼 클릭

2. **쿼리 확인**:
   - Prometheus UI (http://localhost:9090)에서 쿼리 직접 실행
   - 예: `rate(http_requests_total[5m])`

3. **시간 범위 조정**:
   - Grafana 대시보드 우측 상단 시간 선택기 확인
   - "Last 1 hour" 또는 "Last 6 hours"로 설정

### 메모리 사용량이 높을 때

1. **Prometheus 데이터 보존 기간 조정**:
   ```yaml
   # docker-compose.monitoring.yml
   command:
     - '--storage.tsdb.retention.time=15d'  # 30일 → 15일로 감소
   ```

2. **스크래핑 간격 증가**:
   ```yaml
   # prometheus.yml
   scrape_interval: 30s  # 15초 → 30초로 증가
   ```

## 모범 사례

### 1. 알림 설정 (선택사항)

Prometheus Alertmanager를 추가하여 임계값 기반 알림 설정:

```yaml
# alert_rules.yml
groups:
  - name: omypic_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(error_count_total[5m]) > 1
        for: 5m
        annotations:
          summary: "에러 발생률 높음"
```

### 2. 메트릭 레이블 관리

- **카디널리티 주의**: 레이블 값이 무한정 증가하지 않도록 정규화
- **일관성**: 레이블 이름은 snake_case 사용
- **의미**: 비즈니스 로직을 반영하는 의미 있는 레이블 사용

### 3. 백업 전략

```bash
# Prometheus 데이터 백업
docker run --rm -v prometheus_data:/data -v $(pwd):/backup ubuntu tar czf /backup/prometheus_backup.tar.gz /data

# Grafana 데이터 백업
docker run --rm -v grafana_data:/data -v $(pwd):/backup ubuntu tar czf /backup/grafana_backup.tar.gz /data
```

## 면접 대비 핵심 개념

### Prometheus
- **Pull 기반**: 타겟에서 능동적으로 메트릭을 가져옴 (Push 방식 대비 장점)
- **시계열 데이터베이스**: 시간별 메트릭 저장 및 조회 최적화
- **PromQL**: 강력한 쿼리 언어로 집계, 필터링, 계산
- **Service Discovery**: 동적으로 타겟을 발견하고 모니터링

### Grafana
- **데이터 소스 추상화**: Prometheus, InfluxDB, Elasticsearch 등 다양한 소스 지원
- **대시보드 프로비저닝**: 코드로 대시보드 관리 (GitOps)
- **알림 채널**: Slack, Email, PagerDuty 등 통합

### 메트릭 유형
- **Counter**: 누적값 (요청 수, 에러 수)
- **Gauge**: 현재값 (메모리 사용량, 활성 연결 수)
- **Histogram**: 분포 추적 (응답 시간 percentile)
- **Summary**: 클라이언트 측 percentile 계산

### SRE 개념
- **Golden Signals**: 레이턴시, 트래픽, 에러, 포화도
- **SLA/SLO/SLI**: 서비스 수준 목표 및 지표
- **Observability**: 로그, 메트릭, 트레이스 통합

## 종료 및 정리

```bash
# 모니터링 스택 종료
docker-compose -f docker-compose.monitoring.yml down

# 데이터 포함 완전 삭제 (주의!)
docker-compose -f docker-compose.monitoring.yml down -v

# 특정 서비스만 재시작
docker-compose -f docker-compose.monitoring.yml restart grafana
```

## 참고 자료

- [Prometheus 공식 문서](https://prometheus.io/docs/)
- [Grafana 공식 문서](https://grafana.com/docs/)
- [PromQL 쿼리 가이드](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Redis Exporter GitHub](https://github.com/oliver006/redis_exporter)
- [Celery Flower 문서](https://flower.readthedocs.io/)
