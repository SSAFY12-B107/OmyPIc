from locust import HttpUser, task, between, TaskSet
import json
import random
import time
from urllib.parse import quote

class OmyPICUserBehavior(TaskSet):
    # 테스트에 사용할 변수를 저장할 속성들
    user_id = None
    token = None
    problem_id = None
    script_id = None
    test_id = None
    
    # 테스트 사용자 목록 - 실제 테스트 전에 미리 준비한 사용자 데이터
    # 형식: [{"user_id": "...", "access_token": "..."}, ...]
    test_users = [
        # 여기에 미리 준비한 사용자 데이터를 넣어주세요
        # {"user_id": "507f1f77bcf86cd799439011", "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    ]

    def on_start(self):
        """사용자 인증 준비 - 미리 생성된 토큰 사용"""
        # 1. 테스트 사용자가 준비되어 있으면 그 중 하나를 랜덤하게 선택
        if self.test_users:
            test_user = random.choice(self.test_users)
            self.user_id = test_user["user_id"]
            self.token = test_user["access_token"]
            print(f"기존 사용자 선택: {self.user_id}")
            return
            
        # 2. 테스트 사용자가 없는 경우: 실제 환경에서는 다음과 같이 사전 설정 필요
        # 실제 테스트 전에 몇 명의 테스트 계정을 미리 만들고, 각 계정의 토큰을 미리 획득하여
        # test_users 리스트에 추가해야 합니다.
        
        # 아래는 개발/테스트 환경 전용 모의 데이터 생성 (실제 API에 이런 엔드포인트는 없음)
        # 실제 환경에서는 이 부분은 삭제하고 test_users에 미리 데이터를 채워넣어야 함
        mock_data = {
            "auth_provider": "google",
            "mock_token": True,  # 이것은 개발 환경의 특수 플래그일 뿐입니다
            "email": f"test{random.randint(1, 1000)}@example.com"
        }
        
        try:
            # 개발 환경에서만 작동하는 모의 인증 엔드포인트 (실제로는 존재하지 않을 수 있음)
            response = self.client.post("/api/auth/mock-login", json=mock_data)
            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get("user_id")
                self.token = data.get("access_token")
                print(f"모의 사용자 생성: {self.user_id}")
            else:
                print(f"모의 로그인 실패: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"모의 인증 오류: {str(e)}")

    def get_auth_headers(self):
        """인증 헤더 반환"""
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    @task(10)
    def get_problems_by_category(self):
        """카테고리별 문제 조회"""
        if not self.token:
            return
            
        # 여러 카테고리 중 하나를 무작위로 선택
        categories = ["주거", "친구/가족", "여행", "고난도", "빈출", "음식"]
        category = random.choice(categories)
        
        # URL 인코딩이 필요한 경우
        encoded_category = quote(category)
        
        response = self.client.get(
            f"/api/problems/{encoded_category}?skip=0&limit=10",
            headers=self.get_auth_headers()
        )
        
        # 응답에서 문제 ID를 저장 (나중에 상세 조회에 사용)
        if response.status_code == 200:
            problems = response.json()
            if problems and len(problems) > 0:
                problem = random.choice(problems)
                self.problem_id = problem.get("_id")

    @task(8)
    def get_problem_detail(self):
        """문제 상세 조회"""
        if not self.token or not self.problem_id:
            return
            
        self.client.get(
            f"/api/problems/detail/{self.problem_id}",
            headers=self.get_auth_headers()
        )

    @task(6)
    def get_basic_questions(self):
        """기본 질문 조회"""
        if not self.token or not self.problem_id:
            return
            
        self.client.get(
            f"/api/problems/{self.problem_id}/basic-question",
            headers=self.get_auth_headers()
        )

    @task(4)
    def create_custom_questions(self):
        """꼬리 질문 생성"""
        if not self.token or not self.problem_id:
            return
            
        questions_data = {
            "question1": "I usually speak English at work with my colleagues.",
            "question2": "I've been learning English for about 5 years now.",
            "question3": "I find pronunciation the most difficult aspect of English."
        }
        
        self.client.post(
            f"/api/problems/{self.problem_id}/custom-question",
            json=questions_data,
            headers=self.get_auth_headers()
        )

    @task(3)
    def create_script(self):
        """스크립트 생성"""
        if not self.token or not self.problem_id:
            return
            
        script_data = {
            "type": "basic",
            "basic_answers": {
                "answer1": "I live in an apartment in Seoul with my family.",
                "answer2": "The best thing about my neighborhood is the convenient transportation.",
                "answer3": "If I could change one thing, I would add more parks and green spaces."
            }
        }
        
        response = self.client.post(
            f"/api/problems/{self.problem_id}/scripts",
            json=script_data,
            headers=self.get_auth_headers()
        )
        
        # 스크립트 ID 저장 (업데이트에 사용)
        if response.status_code == 201:
            self.script_id = response.json().get("_id")

    @task(5)
    def get_tests_history(self):
        """테스트 내역 조회"""
        if not self.token:
            return
            
        self.client.get(
            "/api/tests/history",
            headers=self.get_auth_headers()
        )

    @task(2)
    def create_test(self):
        """테스트 생성"""
        if not self.token:
            return
            
        # 테스트 유형: 0은 7문제, 1은 15문제, 2는 랜덤 1문제
        test_type = random.randint(0, 2)
        
        response = self.client.post(
            f"/api/tests/{test_type}",
            headers=self.get_auth_headers()
        )
        
        if response.status_code == 200 or response.status_code == 201:
            # 테스트 ID 저장 (나중에 상세 조회에 사용)
            res_data = response.json()
            if "_id" in res_data:
                self.test_id = res_data.get("_id")

    @task(3)
    def get_test_detail(self):
        """테스트 상세 조회"""
        if not self.token or not self.test_id:
            return
            
        self.client.get(
            f"/api/tests/{self.test_id}",
            headers=self.get_auth_headers()
        )

class OmyPICUser(HttpUser):
    tasks = [OmyPICUserBehavior]
    wait_time = between(1, 5)  # 요청 사이 1-5초 대기

# 실행 방법: locust -f locustfile.py --host=http://localhost:8000