// src/pages/auth/AuthCallback.jsx (또는 .tsx)
import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { setUser } from '../../store/authSlice';

function AuthCallback() {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const [status, setStatus] = useState('처리 중...');
  const [error, setError] = useState(null);

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

        // console.log(`code`:code);
        
        setStatus(`코드 확인됨: ${code.substring(0, 10)}...`);
        
        // 2. 백엔드 API 호출하여 토큰 교환
        setStatus('토큰 교환 API 호출 중...');
        const response = await fetch('http://localhost:8000/api/auth/exchange-token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code })
        });
        
        if (!response.ok) {
          const errorText = await response.text();
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
          sessionStorage.access_token = data.access_token;
          console.log('토큰 저장 시도 완료');
          
          // 저장 확인
          const savedToken = sessionStorage.access_token;
          console.log('저장된 토큰 확인:', savedToken ? '성공' : '실패');
          
          if (data.user) {
            // 사용자 정보도 저장
            sessionStorage.user = JSON.stringify(data.user);
            sessionStorage.isOnboarded = data.user.is_onboarded ? 'true' : 'false';
            console.log('사용자 정보 저장됨');
            
            // Redux 스토어에 사용자 정보 저장
            dispatch(setUser(data.user));
            
            setStatus('데이터 저장 완료, 리다이렉트 준비 중...');
            
            // 페이지 이동 전 저장 완료를 위한 지연
            setTimeout(() => {
              if (!data.user.is_onboarded) {
                if (data.user.current_opic_score && data.user.target_opic_score && data.user.target_exam_date) {
                  navigate('/auth/survey');
                } else {
                  navigate('/auth/profile');
                }
              } else {
                navigate('/');
              }
            }, 1000);
          } else {
            setStatus('사용자 정보 없음, 홈으로 이동 중...');
            setTimeout(() => navigate('/'), 1000);
          }
        } catch (storageError) {
          console.error('스토리지 저장 오류:', storageError);
          setStatus(`스토리지 저장 오류: ${storageError.message}`);
          
          // 오류가 있어도 일단 이동은 시도
          setTimeout(() => navigate('/'), 2000);
        }
      } catch (err) {
        console.error('인증 처리 오류:', err);
        setStatus(`처리 오류: ${err.message}`);
        setError(err instanceof Error ? err.message : '인증 처리 중 오류가 발생했습니다');
        
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
        
        <button
          onClick={() => {
            // 저장된 데이터 직접 확인
            const token = sessionStorage.access_token;
            const getToken = sessionStorage.getItem('access_token');
            const user = sessionStorage.user;
            
            alert(`
              세션 스토리지 확인:
              - 토큰(직접): ${token ? '있음' : '없음'}
              - 토큰(getItem): ${getToken ? '있음' : '없음'}
              - 사용자: ${user ? '있음' : '없음'}
            `);
          }}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded"
        >
          저장 상태 확인
        </button>
      </div>
    </div>
  );
}

export default AuthCallback;