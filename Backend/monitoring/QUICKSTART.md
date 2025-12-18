# 모니터링 스택 빠른 시작 가이드

> 5분 안에 모니터링 스택 구동하기

## 1단계: 환경 확인 (30초)

```bash
# 프로젝트 디렉토리 이동
cd c:\Users\ki000\OneDrive\바탕 화면\OmyPIc\Backend

# Docker 실행 확인
docker --version
docker-compose --version
```

## 2단계: 모니터링 스택 실행 (1분)

```bash
# 모니터링 서비스 시작 (백그라운드)
docker-compose -f docker-compose.monitoring.yml up -d

# 상태 확인
docker-compose -f docker-compose.monitoring.yml ps
```

**예상 출력**:
```
NAME                   STATUS              PORTS
omypic_prometheus      Up 30 seconds       0.0.0.0:9090->9090/tcp
omypic_grafana         Up 30 seconds       0.0.0.0:3001->3000/tcp
omypic_redis_exporter  Up 30 seconds       0.0.0.0:9121->9121/tcp
omypic_flower          Up 30 seconds       0.0.0.0:5555->5555/tcp
```

## 3단계: FastAPI 앱 실행 (30초)

```bash
# 로컬 실행
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**메트릭 확인**:
```bash
curl http://localhost:8000/metrics
```

## 4단계: Celery 워커 실행 (30초)

**새 터미널 열기**:

```bash
cd c:\Users\ki000\OneDrive\바탕 화면\OmyPIc\Backend

# Gevent Pool 사용
celery -A celery_worker.celery_app worker --pool=gevent --concurrency=100 --loglevel=info
```

## 5단계: 대시보드 접속 (1분)

### Grafana 대시보드
1. 브라우저에서 http://localhost:3001 접속
2. 로그인: `admin / omypic123`
3. 좌측 메뉴 → Dashboards → Browse
4. "OmyPIC Backend Monitoring" 클릭

### Prometheus UI
- http://localhost:9090
- Status → Targets에서 모든 타겟 "UP" 확인

### Flower (Celery 모니터링)
- http://localhost:5555
- 워커 목록 및 활성 작업 확인

## 6단계: 테스트 트래픽 생성 (선택사항)

```bash
# API 호출 테스트
curl http://localhost:8000/
curl http://localhost:8000/api/tests

# 부하 테스트 (locust 사용)
locust -f locustfile.py --host=http://localhost:8000
```

## 빠른 명령어 모음

```bash
# 모니터링 스택 관리
docker-compose -f docker-compose.monitoring.yml up -d     # 시작
docker-compose -f docker-compose.monitoring.yml down      # 종료
docker-compose -f docker-compose.monitoring.yml restart   # 재시작
docker-compose -f docker-compose.monitoring.yml logs -f   # 로그 확인

# 특정 서비스만 재시작
docker-compose -f docker-compose.monitoring.yml restart grafana
docker-compose -f docker-compose.monitoring.yml restart prometheus

# 메트릭 확인
curl http://localhost:8000/metrics     # FastAPI
curl http://localhost:9121/metrics     # Redis Exporter
curl http://localhost:5555/metrics     # Flower
```

## 문제 해결

### Prometheus 타겟이 DOWN인 경우

```bash
# FastAPI 실행 확인
curl http://localhost:8000/metrics

# Docker 네트워크 확인
docker network inspect omypic_network

# Prometheus 로그 확인
docker-compose -f docker-compose.monitoring.yml logs prometheus
```

### Grafana "No data" 표시

1. Grafana → Configuration → Data Sources → Prometheus → Test 클릭
2. Prometheus UI (http://localhost:9090)에서 쿼리 직접 실행
3. 시간 범위를 "Last 1 hour"로 조정

### Redis Exporter 연결 실패

```bash
# Redis 실행 확인
redis-cli ping

# Redis Exporter 로그
docker-compose -f docker-compose.monitoring.yml logs redis_exporter

# Redis 연결 정보 확인 (.env)
cat .env | grep REDIS_URL
```

## 완전 초기화 (주의!)

```bash
# 모니터링 스택 종료 및 데이터 삭제
docker-compose -f docker-compose.monitoring.yml down -v

# 다시 시작
docker-compose -f docker-compose.monitoring.yml up -d
```

## 다음 단계

- [monitoring/README.md](./README.md): 상세 설명서
- [docs/monitoring_setup.md](../docs/monitoring_setup.md): 면접 대비 가이드

---

*시작하는 데 문제가 있나요? docs/monitoring_setup.md의 "문제 해결" 섹션을 참고하세요.*
