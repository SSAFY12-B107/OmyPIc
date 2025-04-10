from locust import HttpUser, task, between
import os
import base64
import time

# 두 엔드포인트 비교를 위한 사용자 클래스
class AudioProcessingUser(HttpUser):
    wait_time = between(1, 3)  # 1-3초 대기 시간
    
    # 사용자 인증 정보
    user_id = "67e66d465bdadd2334acf0e5"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2N2U2NmQ0NjViZGFkZDIzMzRhY2YwZTUiLCJuYW1lIjoiXHViYTg1XHVkMGQwXHVjODE1XHViM2M0XHViNzdjXHVjNWQwXHViYWJkIiwiYXV0aF9wcm92aWRlciI6Imdvb2dsZSIsImV4cCI6MTc0NDI2MjUyOH0.ZHzbNU6_H5iezVjP3C72GAIEq0W4025tSDlrScQ0IdA"
    
    # 하드코딩된 테스트 ID와 문제 ID (테스트 전에 실제 값으로 업데이트 필요)
    test_id = "67f7555a2c9fe425e668e747"  # <-- 실제 테스트 ID로 교체
    problem_id = "67d97ab2361f78766a3c466f"  # <-- 실제 문제 ID로 교체
    
    # 오디오 파일 내용
    audio_content = None
    audio_filename = "test_audio.mp3"
    
    def on_start(self):
        """테스트 시작 시 초기화"""
        print(f"테스트 시작 - 사용자: {self.user_id}")
        print(f"테스트 ID: {self.test_id}, 문제 ID: {self.problem_id}")
        
        # 오디오 파일 로드
        self.audio_content = self.create_dummy_audio()
    
    def get_auth_headers(self):
        """인증 헤더 반환"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def create_dummy_audio(self):
        """더미 오디오 데이터 생성"""
        try:
            # 테스트 디렉토리에서 오디오 파일 찾기
            test_audio_dir = os.path.join(os.path.dirname(__file__), "test_data")
            if os.path.exists(test_audio_dir):
                audio_files = [f for f in os.listdir(test_audio_dir) if f.endswith('.mp3')]
                if audio_files:
                    audio_file = audio_files[0]
                    audio_path = os.path.join(test_audio_dir, audio_file)
                    with open(audio_path, "rb") as f:
                        return f.read()
        except Exception as e:
            print(f"오디오 파일 로드 중 오류: {str(e)}")
        
        # 파일이 없거나 로드 실패 시 더미 데이터 생성
        print("더미 오디오 데이터 생성")
        return b"This is dummy audio data for testing purposes" * 1000
    
    @task
    def test_standard_endpoint(self):
        """표준 방식 엔드포인트 테스트"""
        # 멀티파트 파일 준비
        files = {"audio_file": (self.audio_filename, self.audio_content, "audio/mpeg")}
        data = {"is_last_problem": "false"}
        
        # 표준 방식으로 요청 보내기
        try:
            response = self.client.post(
                f"/api/tests/{self.test_id}/record/{self.problem_id}",
                files=files,
                data=data,
                headers=self.get_auth_headers(),
                name="Standard Endpoint"
            )
            print(f"표준 방식 응답: {response.status_code}")
        except Exception as e:
            print(f"표준 엔드포인트 오류: {str(e)}")
    
    @task
    def test_celery_endpoint(self):
        """Celery 방식 엔드포인트 테스트"""
        # 멀티파트 파일 준비
        files = {"audio_file": (self.audio_filename, self.audio_content, "audio/mpeg")}
        data = {"is_last_problem": "false"}
        
        # Celery 방식으로 요청 보내기
        try:
            response = self.client.post(
                f"/api/tests/{self.test_id}/record-celery/{self.problem_id}",
                files=files,
                data=data,
                headers=self.get_auth_headers(),
                name="Celery Endpoint",
                timeout=30  # 타임아웃 설정 추가
            )
            print(f"Celery 방식 응답: {response.status_code}, 내용: {response.text[:100]}")
        except Exception as e:
            print(f"Celery 엔드포인트 오류 상세: {str(e)}, 타입: {type(e)}")


# 실행 방법: 
# 1. 실제 테스트 ID와 문제 ID로 코드 업데이트 (필수!)
#    - 먼저 테스트를 하나 생성하고 ID를 복사
#    - 코드 상단의 test_id와 problem_id를 실제 값으로 변경
# 
# 2. Locust 실행: 
#    locust -f Backend/locustfile.py --host=http://localhost:8000
#
# 3. 브라우저에서 http://localhost:8089 접속
#    - 사용자 수: 동시 요청할 사용자 수 설정 (예: 20명)
#    - Spawn rate: 초당 사용자 증가율 (예: 10)
#    - Host: 테스트 대상 서버 URL