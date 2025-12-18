// OmyPIC Backend K6 부하 테스트
// 실행: k6 run tests/load_test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// 커스텀 메트릭
const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');

// 테스트 시나리오 설정
export const options = {
  scenarios: {
    // 시나리오 1: 점진적 부하 증가
    ramp_up: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 10 },  // 30초 동안 10명까지 증가
        { duration: '1m', target: 10 },   // 1분 동안 10명 유지
        { duration: '30s', target: 50 },  // 30초 동안 50명까지 증가
        { duration: '1m', target: 50 },   // 1분 동안 50명 유지
        { duration: '30s', target: 0 },   // 30초 동안 0명으로 감소
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<5000'],  // 95% 요청이 5초 이내
    errors: ['rate<0.1'],                // 에러율 10% 미만
  },
};

// Docker 내부에서는 'fastapi', 로컬에서는 'localhost' 사용
const BASE_URL = __ENV.BASE_URL || 'http://fastapi:8000';

// 테스트용 더미 JWT 토큰 (실제 테스트 시 유효한 토큰으로 교체)
const AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test';

// 헬스체크 테스트
function healthCheck() {
  const res = http.get(`${BASE_URL}/health`);
  check(res, {
    'health check status is 200': (r) => r.status === 200,
  });
  return res.status === 200;
}

// API 엔드포인트 테스트
function testEndpoints() {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${AUTH_TOKEN}`,
  };

  // 1. 헬스체크
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, { 'health: status 200': (r) => r.status === 200 });
  apiLatency.add(healthRes.timings.duration);

  // 2. 메트릭 엔드포인트 (Prometheus)
  const metricsRes = http.get(`${BASE_URL}/metrics`);
  check(metricsRes, { 'metrics: status 200': (r) => r.status === 200 });

  // 3. API 문서
  const docsRes = http.get(`${BASE_URL}/docs`);
  check(docsRes, { 'docs: status 200': (r) => r.status === 200 });

  // 에러 체크
  errorRate.add(healthRes.status !== 200);
}

// 메인 테스트 함수
export default function () {
  testEndpoints();
  sleep(1);  // 1초 대기 (실제 사용자 행동 시뮬레이션)
}

// 테스트 종료 후 요약
export function handleSummary(data) {
  console.log('\n========== 부하 테스트 결과 ==========');
  console.log(`총 요청 수: ${data.metrics.http_reqs.values.count}`);
  console.log(`평균 응답 시간: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms`);
  console.log(`P95 응답 시간: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms`);
  console.log(`에러율: ${(data.metrics.errors?.values?.rate * 100 || 0).toFixed(2)}%`);
  console.log('======================================\n');

  return {
    'stdout': JSON.stringify(data, null, 2),
  };
}
