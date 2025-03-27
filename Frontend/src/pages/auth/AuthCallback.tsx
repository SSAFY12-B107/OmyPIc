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
  
  // 요청이 이미 진행 중인지 추적하는 ref
  const isCalledRef = useRef(false);

  // 스피너 스타일 정의 - 컴포넌트 안에서 정의
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
          
          // 페이지 이동 전 지연
          if (!data.user.is_onboarded) {
            // 온보딩이 필요한 경우
            navigate('/auth/profile');
          } else {
            // 온보딩이 완료된 경우 홈으로
            navigate('/');
          }
        } else {
          setTimeout(() => navigate('/'), 500);
        }
      } catch (storageError) {
        console.error('스토리지 저장 오류:', storageError);
        setTimeout(() => navigate('/'), 1000);
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
      
      {/* 항상 스피너만 표시 */}
      <div style={spinnerStyle}></div>
    </div>
  );
}

export default AuthCallback;