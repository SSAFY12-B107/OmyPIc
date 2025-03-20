// src/routes/AuthRoutes.tsx
import { Route, Routes } from 'react-router-dom';
import Login from '../pages/auth/Login';
import Profile from '../pages/auth/Profile';
import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

// 인증 콜백 처리 컴포넌트
function AuthHandler() {
  const navigate = useNavigate();
  const location = useLocation();
  
  useEffect(() => {
    // URL 쿼리 파라미터에서 토큰과 사용자 정보 가져오기
    const searchParams = new URLSearchParams(location.search);
    const accessToken = searchParams.get('access_token');
    const refreshToken = searchParams.get('refresh_token');
    const userJson = searchParams.get('user');
    
    if (accessToken) {
      // 세션 스토리지에 토큰 저장
      sessionStorage.setItem('access_token', accessToken);
      
      if (refreshToken) {
        sessionStorage.setItem('refresh_token', refreshToken);
      }
      
      // 사용자 정보가 있다면 저장
      if (userJson) {
        try {
          const userObj = JSON.parse(decodeURIComponent(userJson));
          sessionStorage.setItem('user', JSON.stringify(userObj));
          
          // 온보딩 여부에 따라 리다이렉트
          if (!userObj.is_onboarded) {
            navigate('/profile'); // 온보딩이 필요한 경우 프로필 페이지로
          } else {
            navigate('/'); // 온보딩이 완료된 경우 홈으로
          }
        } catch (error) {
          console.error('사용자 정보 파싱 오류:', error);
          navigate('/login');
        }
      } else {
        navigate('/');
      }
    } else {
      // 토큰이 없는 경우 로그인 페이지로
      navigate('/login');
    }
  }, [location, navigate]);
  
  return (
    <div>
      <div className="spinner"></div>
      <p>인증 처리 중...</p>
    </div>
  );
}

// 인증 관련 라우트 정의
const AuthRoutes = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/profile" element={<Profile />} />
      <Route path="/auth/callback" element={<AuthHandler />} />
    </Routes>
  );
};

export default AuthRoutes;