import { useEffect, useState, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useMutation } from "@tanstack/react-query";
import { useDispatch } from 'react-redux';
import { setUser } from '../../store/authSlice';
import apiClient from '@/api/apiClient';

function AuthCallback() {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // 요청이 이미 진행 중인지 추적하는 ref
  const isCalledRef = useRef(false);

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
      console.log('response', response);
      
      try {
        // 액세스 토큰 저장
        sessionStorage.setItem('access_token', data.access_token);
        
        if (data.user) {
          // isOnboarded 정보 저장
          sessionStorage.setItem('isOnboarded', data.user.is_onboarded ? 'true' : 'false');
          
          // Redux 스토어에 사용자 정보 저장
          dispatch(setUser(data.user));
          
          // 로딩 상태 업데이트
          setIsLoading(false);
          
          // 페이지 이동 전 지연
          if (!data.user.is_onboarded) {
            // 온보딩이 필요한 경우 프로필 페이지로 이동
            navigate('/auth/profile');
          } else {
            // 온보딩이 완료된 경우 홈으로 이동
            navigate('/');
          }
        } else {
          // 사용자 데이터가 없는 경우
          setIsLoading(false);
          setError('사용자 정보를 찾을 수 없습니다');
          setTimeout(() => navigate('/auth/login'), 1000);
        }
      } catch (storageError) {
        console.error('스토리지 저장 오류:', storageError);
        setIsLoading(false);
        setError('사용자 정보 저장 중 오류가 발생했습니다');
        setTimeout(() => navigate('/auth/login'), 1000);
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
      
      // 실패 시 로그인 페이지로 이동
      setTimeout(() => {
        navigate('/auth/login');
      }, 1000);
    }
  });

  async function handleAuth() {
    // 이미 호출된 경우 중복 실행 방지
    if (isCalledRef.current) return;
    isCalledRef.current = true;
    
    try {
      // URL에서 code 파라미터 추출
      const searchParams = new URLSearchParams(location.search);
      const code = searchParams.get('code');
      console.log('Code from URL:', code);
      
      if (!code) {
        setTimeout(() => navigate('/auth/login'), 1000);
        return;
      }
      
      // TanStack Query mutation 실행
      exchangeTokenMutation.mutate(code);
      
    } catch (err) {
      console.error('인증 처리 오류:', err);
      const errorMessage = err instanceof Error ? err.message : '인증 처리 중 오류가 발생했습니다';
      
      setTimeout(() => navigate('/auth/login'), 1000);
    }
  }
  
  useEffect(() => {
    handleAuth();
    
    // cleanup 함수 추가
    return () => {
      isCalledRef.current = false;
    };
  }, []);

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