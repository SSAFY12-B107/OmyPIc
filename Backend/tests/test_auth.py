import pytest

class TestEnvironmentSetup:
    '''
    테스트 환경 설정 확인
    
    pytest를 실행하면 이 테스트들이 먼저 돌아가요.
    모두 통과하면 환경 설정 성공
    '''
    def test_pytest_works(self):
        '''
        pytest가 정상 동작하는지 확인
        
        assert True는 항상 성공해요.
        이 테스트가 실패하면 pytest 자체에 문제가 있는 거예요.
        '''
        assert True
        
    def test_fixture_mock_db(self, mock_db):
        '''
        mock_db fixture가 잘 동작하는지 확인
        conftest.py에서 정의한 mock_db가 자동으로 주입돼요.
        '''
        # mock_db가 None이 아닌지 확인
        assert mock_db is not None

         # users 컬렉션이 있는지 확인
        assert mock_db.users is not None
        
        # temp_codes 컬렉션이 있는지 확인
        assert mock_db.temp_codes is not None
        
        print("mock_db fixture 정상 동작!")
        
    def test_fixture_sample_users(self, sample_google_user,sample_naver_user):
        """
        샘플 사용자 데이터 fixture 확인
        """
        # Google User data 확인
        assert "sub" in sample_google_user
        assert "email" in sample_google_user
        
        # Naver 사용자 데이터 확인 (response 안에 있음)
        assert "response" in sample_naver_user
        assert "id" in sample_naver_user["response"]

        print("샘플 사용자 데이터 fixture 정상!")
        
    def test_fixture_create_tokens(self, create_test_tokens):
        """
        JWT 토큰 생성 fixture 확인
        """
        access_token, refresh_token = create_test_tokens("test_user_id")
        
        # 토큰이 문자열인지 확인
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        
        # 토큰이 비어있지 않은지 확인
        assert len(access_token) > 0
        assert len(refresh_token) > 0
        
        print(f" Access Token 생성: {access_token[:50]}...")
        print(f" Refresh Token 생성: {refresh_token[:50]}...")
 
# Test Example
class TestAsyncExample:
    """
    async 테스트 예시
    
    FastAPI는 비동기로 동작하기 때문에,
    테스트도 비동기로 작성해야 해요.
    """
    
    @pytest.mark.asyncio
    async def test_async_mock_db(self, mock_db):
        """
        비동기 mock_db 호출 테스트
        
        @pytest.mark.asyncio 데코레이터가 있으면
        pytest가 이 함수를 비동기로 실행해요.
        """
        # 비동기 호출 (await 사용)
        result = await mock_db.users.find_one({"email": "test@test.com"})
        
        # 기본값은 None (conftest.py에서 설정)
        assert result is None
        
        print(" 비동기 mock_db 호출 성공!")
