// src/routes/AuthRoutes.tsx
import { Route, Routes } from 'react-router-dom';
import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { setUser, setError } from '../store/authSlice';
import Login from '../pages/auth/Login';
import Profile from '../pages/auth/Profile';
import Survey from '../pages/auth/Survey';
import Loading from '../components/common/Loading'; // 로딩 컴포넌트 필요

// 인증 콜백 처리 컴포넌트
function AuthHandler() {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  
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
          
          // 세션 스토리지에 사용자 정보 저장
          sessionStorage.setItem('user', JSON.stringify(userObj));
          sessionStorage.setItem('isOnboarded', userObj.is_onboarded ? 'true' : 'false');
          
          // Redux 스토어에 사용자 정보 저장
          dispatch(setUser(userObj));
          
          // 온보딩 여부에 따라 리다이렉트
          if (!userObj.is_onboarded) {
            // 프로필 정보 확인
            if (userObj.current_opic_score && userObj.target_opic_score && userObj.target_exam_date) {
              navigate('/auth/survey'); // 이미 프로필 정보가 있으면 서베이로
            } else {
              navigate('/auth/profile'); // 프로필 정보가 없으면 프로필 페이지로
            }
          } else {
            navigate('/'); // 온보딩이 완료된 경우 홈으로
          }
        } catch (error) {
          console.error('사용자 정보 파싱 오류:', error);
          dispatch(setError('사용자 정보를 처리하는 중 오류가 발생했습니다'));
          navigate('/auth/login');
        }
      } else {
        // 토큰은 있지만 사용자 정보가 없는 경우
        // 백엔드에서 사용자 정보를 가져오는 API 호출이 필요할 수 있음
        navigate('/');
      }
    } else {
      // 토큰이 없는 경우 로그인 페이지로
      navigate('/auth/login');
    }
  }, [location, navigate, dispatch]);
  
  // 로딩 화면 표시
  return <Loading message="인증 처리 중..." />;
}

// 인증 관련 라우트 정의
const AuthRoutes = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/profile" element={<Profile />} />
      <Route path="/survey" element={<Survey />} />
      <Route path="/callback" element={<AuthHandler />} />
      <Route path="/google/callback" element={<AuthHandler />} />
      <Route path="/naver/callback" element={<AuthHandler />} />
    </Routes>
  );
};

export default AuthRoutes;