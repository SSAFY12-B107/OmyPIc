// src/pages/auth/AuthCallback.tsx
import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { setUser } from '../../store/authSlice';

function AuthCallback() {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const [status, setStatus] = useState<string>('처리 중...');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function handleAuth() {
      try {
        // 1. URL에서 code 파라미터 추출
        const searchParams = new URLSearchParams(location.search);
        const code = searchParams.get('code');
        
        if (!code) {
          setStatus('인증 코드가 없습니다');
          setError('인증 코드가 없습니다');
          return;
        }
        
        setStatus(`코드 확인됨: ${code.substring(0, 10)}...`);
        
        // 2. 백엔드 API 호출하여 토큰 교환 - 요청 방식 수정
        setStatus('토큰 교환 API 호출 중...');
        
        // 요청 데이터 상세 로깅
        console.log('인증 코드 전송:', { code });
        
        const response = await fetch('http://localhost:8000/api/auth/exchange-token', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          credentials: 'include', // 쿠키 포함
          body: JSON.stringify({ 
            code,
            redirect_uri: window.location.origin + '/auth/callback' // 리다이렉트 URI 추가
          })
        });
        
        // 응답 상태 로깅
        console.log('API 응답 상태:', response.status, response.statusText);
        
        if (!response.ok) {
          let errorText;
          try {
            // JSON 형태로 오류 응답 파싱 시도
            const errorData = await response.json();
            errorText = JSON.stringify(errorData);
            console.error('API 오류 상세 (JSON):', errorData);
          } catch (e) {
            // 일반 텍스트로 파싱
            errorText = await response.text();
            console.error('API 오류 상세 (텍스트):', errorText);
          }
          
          setStatus(`API 오류: ${response.status}`);
          setError(`API 오류: ${errorText}`);
          return;
        }
        
        // 3. API 응답 파싱
        const data = await response.json();
        setStatus('토큰 교환 성공, 저장 시도 중...');
        console.log('받은 데이터:', data);
        
        // 4. 세션 스토리지에 직접 데이터 저장
        try {
          // 프로퍼티 방식으로 저장
          sessionStorage.setItem('access_token', data.access_token);
          console.log('토큰 저장 시도 완료');
          
          // 저장 확인
          const savedToken = sessionStorage.getItem('access_token');
          console.log('저장된 토큰 확인:', savedToken ? '성공' : '실패');
          
          if (data.user) {
            // 사용자 정보도 저장
            sessionStorage.setItem('isOnboarded', data.user.is_onboarded ? 'true' : 'false');
            console.log('사용자 정보 저장됨:', data.user);
            
            // Redux 스토어에 사용자 정보 저장
            dispatch(setUser(data.user));
            
            setStatus('데이터 저장 완료, 리다이렉트 준비 중...');
            
            // 페이지 이동 전 저장 완료를 위한 지연
            setTimeout(() => {
              if (!data.user.is_onboarded) {
                // 온보딩이 필요한 경우
                if (data.user.current_opic_score && data.user.target_opic_score && data.user.target_exam_date) {
                  // 이미 프로필 정보가 있으면 설문 페이지로
                  navigate('/auth/survey');
                } else {
                  // 프로필 정보가 없으면 프로필 페이지로
                  navigate('/auth/profile');
                }
              } else {
                // 온보딩이 완료된 경우 홈으로
                navigate('/');
              }
            }, 1000);
          } else {
            setStatus('사용자 정보 없음, 홈으로 이동 중...');
            setTimeout(() => navigate('/'), 1000);
          }
        } catch (storageError) {
          console.error('스토리지 저장 오류:', storageError);
          setStatus(`스토리지 저장 오류: ${storageError instanceof Error ? storageError.message : String(storageError)}`);
          
          // 오류가 있어도 일단 이동은 시도
          setTimeout(() => navigate('/'), 2000);
        }
      } catch (err) {
        console.error('인증 처리 오류:', err);
        const errorMessage = err instanceof Error ? err.message : '인증 처리 중 오류가 발생했습니다';
        setStatus(`처리 오류: ${errorMessage}`);
        setError(errorMessage);
        
        setTimeout(() => {
          navigate('/auth/login');
        }, 3000);
      }
    }
    
    handleAuth();
  }, [location, navigate, dispatch]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <div className="text-center">
        <h2 className="text-xl font-semibold mb-4">로그인 처리 중</h2>
        <p className="mb-4">{status}</p>
        
        {error && (
          <div className="text-red-500 mb-4">
            <p>오류: {error}</p>
            <p className="text-sm mt-2">잠시 후 로그인 페이지로 이동합니다...</p>
          </div>
        )}
        
        <div className="flex flex-col space-y-4">
          <button
            onClick={() => {
              // 저장된 데이터 직접 확인
              const token = sessionStorage.getItem('access_token');
              const isOnboarded = sessionStorage.getItem('isOnboarded');
              
              alert(`
                세션 스토리지 확인:
                - 토큰: ${token ? '있음' : '없음'}
                - 온보딩 상태: ${isOnboarded || '없음'}
              `);
            }}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            저장 상태 확인
          </button>
          
          <button
            onClick={() => navigate('/auth/login')}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            로그인 페이지로 이동
          </button>
        </div>
      </div>
    </div>
  );
}

export default AuthCallback;