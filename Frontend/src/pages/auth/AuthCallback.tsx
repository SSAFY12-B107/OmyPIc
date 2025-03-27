import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { useMutation } from '@tanstack/react-query';
import { setUser } from '../../store/authSlice';
import apiClient from '../../api/apiClient';

function AuthCallback() {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 스피너 스타일 정의
  const spinnerStyle = {
    width: '40px',
    height: '40px',
    border: '3px solid rgba(94, 94, 94, 0.3)',
    borderRadius: '50%',
    borderTopColor: 'rgba(94, 94, 94, 0.8)',
    animation: 'spin 1s ease-in-out infinite',
    margin: '0 auto'
  };

  // TanStack Query를 사용한 토큰 교환 mutation
  const exchangeTokenMutation = useMutation({
    mutationFn: async (code: string) => {
      return await apiClient.post('/auth/exchange-token', { code });
    },
    onSuccess: (response) => {
      const data = response.data;
      
      try {
        // 액세스 토큰 저장
        sessionStorage.setItem('access_token', data.access_token);
        
        if (data.user) {
          // 사용자 정보 저장
          sessionStorage.setItem('isOnboarded', data.user.is_onboarded ? 'true' : 'false');
          
          // Redux 스토어에 사용자 정보 저장
          dispatch(setUser(data.user));
          
          // 페이지 이동 전 지연
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
          }, 500);
        } else {
          setTimeout(() => navigate('/'), 500);
        }
      } catch (storageError) {
        console.error('스토리지 저장 오류:', storageError);
        setError('사용자 정보 저장 중 오류가 발생했습니다');
        setTimeout(() => navigate('/'), 1000);
      } finally {
        setIsLoading(false);
      }
    },
    onError: (error: any) => {
      console.error('인증 오류:', error);
      
      let errorMessage = '인증 처리 중 오류가 발생했습니다';
      if (error.response?.data) {
        errorMessage = typeof error.response.data === 'object' 
          ? JSON.stringify(error.response.data) 
          : error.response.data;
      }
      
      setError(errorMessage);
      setIsLoading(false);
      
      // 실패 시 로그인 페이지로 이동
      setTimeout(() => {
        navigate('/auth/login');
      }, 2000);
    }
  });

  useEffect(() => {
    async function handleAuth() {
      try {
        // URL에서 code 파라미터 추출
        const searchParams = new URLSearchParams(location.search);
        const code = searchParams.get('code');
        
        if (!code) {
          setError('인증 코드가 없습니다');
          setIsLoading(false);
          setTimeout(() => navigate('/auth/login'), 2000);
          return;
        }
        
        // TanStack Query mutation 실행
        exchangeTokenMutation.mutate(code);
        
      } catch (err) {
        console.error('인증 처리 오류:', err);
        const errorMessage = err instanceof Error ? err.message : '인증 처리 중 오류가 발생했습니다';
        setError(errorMessage);
        setIsLoading(false);
        
        setTimeout(() => {
          navigate('/auth/login');
        }, 2000);
      }
    }
    
    handleAuth();
  }, [location, navigate, exchangeTokenMutation]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      {/* 애니메이션 keyframes 추가 */}
      <style>
        {`
          @keyframes spin {
            to {
              transform: rotate(360deg);
            }
          }
        `}
      </style>
      
      <div className="text-center">
        {/* 스피너 표시 */}
        {isLoading && <div style={spinnerStyle}></div>}
        
        {/* 로딩 메시지 */}
        {isLoading && <p className="mt-4 text-gray-600">로그인 처리 중...</p>}
        
        {/* 에러가 있을 경우 표시 */}
        {error && (
          <p className="mt-2 text-red-600">
            {error}
          </p>
        )}
      </div>
    </div>
  );
}

export default AuthCallback;