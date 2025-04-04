import { useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { HeaderProvider } from "./contexts/HeaderContext";
import NavigationInitializer from './components/common/NavigationInitializer';
import ReactGA from "react-ga4";
import { hotjar } from 'react-hotjar';
import {
  PrivateRoute,
  PublicRoute,
  OnboardingRoute,
} from "./routes/ProtectedRoutes";
import AndroidKakaoTalkRedirect from "./components/common/AndroidKakaoTalkRedirect";

import Header from "./components/common/Header";
import Home from "./pages/home/Home";
import Login from "./pages/auth/Login";
import Survey from "./pages/auth/Survey";
import Profile from "./pages/auth/Profile";
import TestMain from "./pages/test/TestMain";
import TestExam from "./pages/test/TestExam";
import FeedBack from "./pages/test/FeedBack";
import ScriptMain from "./pages/script/ScriptMain";
import ScriptList from "./pages/script/ScriptList";
import ScriptDetail from "./pages/script/ScriptDetail";
import ScriptWrite from "./pages/script/ScriptWrite";
import AuthCallback from "./pages/auth/AuthCallback";
import NotFound from "./pages/NotFound";
import RouteTracker from "./components/common/RouteTracker";
import { useAnalytics } from "./hooks/useAnalytics";

function App() {
  const { initGA } = useAnalytics();

  useEffect(() => {
    // GA 초기화
    initGA();

    // Hotjar 초기화 - 개발 환경에서는 실행하지 않음
    if (import.meta.env.MODE !== 'development') {
      const hotjarId = import.meta.env.VITE_HOTJAR_ID;
      
      if (hotjarId) {
        hotjar.initialize({
          id: Number(hotjarId),
          sv: 6
        });
      }
    }
    
    // 브라우저 종료/탭 닫기 추적
    const win = window as any;
    const doc = document as any;

    const handleBeforeUnload = () => {
      const currentPath = win.location.pathname;
      ReactGA.event({
        category: "Exit",
        action: "Browser Close",
        label: currentPath,
      });
    };

    // 탭 비활성화 추적
    const handleVisibilityChange = () => {
      const currentPath = win.location.pathname;

      if (doc.visibilityState === "hidden") {
        ReactGA.event({
          category: "Exit",
          action: "Tab Hidden",
          label: currentPath,
        });
      } else if (doc.visibilityState === "visible") {
        ReactGA.event({
          category: "Engagement",
          action: "Tab Visible",
          label: currentPath,
        });
      }
    };

    // 이벤트 리스너 등록
    win.addEventListener("beforeunload", handleBeforeUnload);
    doc.addEventListener("visibilitychange", handleVisibilityChange);

    // 컴포넌트 언마운트 시 이벤트 리스너 제거
    return () => {
      win.removeEventListener("beforeunload", handleBeforeUnload);
      doc.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [initGA]);

  return (
    <BrowserRouter>
      {/* API 클라이언트에서 사용할 네비게이션 함수를 설정하는 컴포넌트 */}
      <NavigationInitializer />
      
      <AndroidKakaoTalkRedirect>
        <HeaderProvider>
          {/* 헤더는 한 번만 선언하고, 모든 설정은 Context를 통해 관리됨 */}
          <Header />

          {/* GA 페이지 추적 컴포넌트 */}
          <RouteTracker />

          <Routes>
            {/* 로그인, 온보딩 완료된 사용자만 접근 가능 */}
            <Route element={<PrivateRoute />}>
              {/* 루트 경로를 모의고사 페이지로 변경 */}
              <Route path="/" element={<Navigate to="/tests" replace />} />
              
              {/* 기존 홈페이지를 /home 경로로 이동 */}
              <Route path="/home" element={<Home />} />

              {/* Test 관련 라우트 */}
              <Route path="/tests" element={<TestMain />} />
              <Route path="/tests/practice" element={<TestExam />} />
              <Route path="/tests/feedback/:test_pk" element={<FeedBack />} />

              {/* Script 관련 라우트 */}
              <Route path="/scripts" element={<ScriptMain />} />
              <Route path="/scripts/:category" element={<ScriptList />} />
              <Route
                path="/scripts/:category/:problemId"
                element={<ScriptDetail />}
              />
              <Route
                path="/scripts/:category/:problemId/write"
                element={<ScriptWrite />}
              />
            </Route>

            {/* 로그인되지 않은 사용자만 접근 가능 */}
            <Route element={<PublicRoute />}>
              <Route path="/auth/login" element={<Login />} />
              <Route path="/callback" element={<AuthCallback />} />
            </Route>

            {/* 온보딩 페이지들 - 로그인했지만 온보딩 미완료 사용자만 접근 가능 */}
            <Route element={<OnboardingRoute />}>
              <Route path="/auth/profile" element={<Profile />} />
              <Route path="/auth/survey" element={<Survey />} />
            </Route>

            {/* 404 페이지 */}
            <Route path="*" element={<NotFound/>} />
          </Routes>
        </HeaderProvider>
      </AndroidKakaoTalkRedirect>
    </BrowserRouter>
  );
}

export default App;
