// src/routes/ProtectedRoutes.tsx
import { Navigate, Outlet } from 'react-router-dom';

// 온보딩 완료된 사용자만 접근 가능한 라우트
export const PrivateRoute = () => {
  const accessToken = sessionStorage.getItem('access_token');
  const isOnboarded = sessionStorage.getItem('isOnboarded') === 'true';

  if (!accessToken) {
    return <Navigate to="/auth/login" replace />;
  }

  if (!isOnboarded) {
    // 온보딩이 필요한 경우 프로필 페이지로 리다이렉트
    return <Navigate to="/auth/profile" replace />;
  }

  return <Outlet />;
};

// 로그인되지 않은 사용자만 접근 가능한 라우트
export const PublicRoute = () => {
  const accessToken = sessionStorage.getItem('access_token');
  const isOnboarded = sessionStorage.getItem('isOnboarded') === 'true';

  if (accessToken) {
    if (!isOnboarded) {
      return <Navigate to="/auth/profile" replace />;
    }
    
    // 홈(/)에서 모의고사 메인(/tests)으로 변경
    return <Navigate to="/tests" replace />;
  }

  return <Outlet />;
};

// 온보딩 페이지들을 위한 라우트 (프로필 및 서베이 포함)
export const OnboardingRoute = () => {
  const accessToken = sessionStorage.getItem('access_token');
  const isOnboarded = sessionStorage.getItem('isOnboarded') === 'true';

  if (!accessToken) {
    return <Navigate to="/auth/login" replace />;
  }

  if (isOnboarded) {
    // 홈(/)에서 모의고사 메인(/tests)으로 변경
    return <Navigate to="/tests" replace />;
  }

  return <Outlet />;
};