import requests
import json
import webbrowser
import os
import time
from urllib.parse import urlparse, parse_qs

# 테스트 사용자를 준비하는 스크립트
# 이 스크립트는 실제 소셜 로그인을 통해 테스트 사용자를 생성하고 토큰을 획득합니다

# 서버 설정
API_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"  # 프론트엔드 URL

# 결과 저장 파일
USERS_FILE = "test_users.json"

def create_test_user():
    """
    소셜 로그인을 통해 테스트 사용자 생성
    
    1. 소셜 로그인 URL을 열어 브라우저에서 수동으로 로그인합니다
    2. 콜백 URL에서 코드를 획득합니다
    3. 코드를 토큰으로 교환합니다
    4. 사용자 ID와 토큰을 저장합니다
    """
    # 소셜 로그인 URL 열기
    login_url = f"{API_URL}/api/auth/google/login"
    print(f"소셜 로그인 URL을 엽니다: {login_url}")
    print("브라우저가 열리면 소셜 계정으로 로그인해 주세요.")
    print("로그인 후 리디렉션 URL에서 코드를 수동으로 복사해야 합니다.")
    
    webbrowser.open(login_url)
    
    # 사용자로부터 콜백 URL 또는 코드 입력받기
    print("\n로그인 후 리디렉션된 URL을 입력하세요 (또는 code= 다음의 값):")
    callback_input = input("> ")
    
    # 입력이 URL인지 코드인지 확인
    if callback_input.startswith("http"):
        # URL에서 코드 추출
        parsed_url = urlparse(callback_input)
        params = parse_qs(parsed_url.query)
        code = params.get("code", [""])[0]
    else:
        # 직접 코드가 입력된 경우
        code = callback_input
    
    if not code:
        print("유효한 코드를 찾을 수 없습니다. 다시 시도해 주세요.")
        return None
    
    # 코드를 토큰으로 교환
    print(f"코드 획득 성공: {code[:10]}... (잘림)")
    print("토큰으로 교환 중...")
    
    try:
        response = requests.post(
            f"{API_URL}/api/auth/exchange-token",
            json={"code": code}
        )
        
        if response.status_code != 200:
            print(f"토큰 교환 실패 ({response.status_code}): {response.text}")
            return None
        
        data = response.json()
        
        # 응답에서 필요한 정보 추출
        access_token = data.get("access_token")
        user_data = data.get("user", {})
        user_id = user_data.get("_id")
        
        print(f"토큰 획득 성공!")
        print(f"사용자 ID: {user_id}")
        
        # 사용자 정보 저장
        user_info = {
            "user_id": user_id,
            "access_token": access_token,
            "name": user_data.get("name", "")
        }
        
        return user_info
    
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return None

def main():
    """메인 함수"""
    print("테스트 사용자 준비를 시작합니다.")
    print("이 과정에서는 브라우저를 통한 실제 소셜 로그인이 필요합니다.")
    
    # 테스트 사용자 목록 초기화
    test_users = []
    
    # 기존 파일이 있으면 로드
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                test_users = json.load(f)
            print(f"기존 테스트 사용자 {len(test_users)}명을 로드했습니다.")
        except Exception as e:
            print(f"기존 파일 로드 중 오류: {str(e)}")
    
    # 몇 명의 테스트 사용자를 생성할지 물어보기
    try:
        num_users = int(input("몇 명의 테스트 사용자를 더 생성하시겠습니까? "))
    except ValueError:
        num_users = 1
        print("유효하지 않은 입력, 기본값 1로 설정합니다.")
    
    # 테스트 사용자 생성
    for i in range(num_users):
        print(f"\n테스트 사용자 {i+1}/{num_users} 생성 중...")
        user_info = create_test_user()
        
        if user_info:
            # 중복 검사
            is_duplicate = False
            for existing_user in test_users:
                if existing_user["user_id"] == user_info["user_id"]:
                    is_duplicate = True
                    print("이미 존재하는 사용자입니다. 토큰을 업데이트합니다.")
                    existing_user["access_token"] = user_info["access_token"]
                    break
            
            if not is_duplicate:
                test_users.append(user_info)
                print(f"테스트 사용자 #{len(test_users)}을(를) 추가했습니다.")
            
            # 각 사용자 생성 후 저장
            with open(USERS_FILE, "w") as f:
                json.dump(test_users, f, indent=2)
            
            print(f"테스트 사용자 정보를 {USERS_FILE}에 저장했습니다.")
        else:
            print("사용자 생성에 실패했습니다.")
        
        # 다음 사용자 생성 전 잠시 대기 (API 제한 방지)
        if i < num_users - 1:
            print("다음 사용자 생성을 위해 5초 대기...")
            time.sleep(5)
    
    print(f"\n총 {len(test_users)}명의 테스트 사용자가 준비되었습니다.")
    print(f"생성된 테스트 사용자는 locustfile-omypic-oauth.py의 test_users 리스트에 추가해 주세요.")

if __name__ == "__main__":
    main()