import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HeaderProvider } from "./contexts/HeaderContext";

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


function App() {
  return (
    <BrowserRouter>
    <HeaderProvider>
      {/* 헤더는 한 번만 선언하고, 모든 설정은 Context를 통해 관리됨 */}
      <Header />
      
      <Routes>
        <Route path="/" element={<Home />} />

        {/* Auth 관련 라우트 */}
        <Route path="/auth/login" element={<Login />} />
        <Route path="/auth/survey" element={<Survey />} />
        <Route path="/auth/profile" element={<Profile />} />
        <Route path="/callback" element={<AuthCallback />} />

        {/* Test 관련 라우트 */}
        <Route path="/tests" element={<TestMain />} />
        <Route path="/tests/practice" element={<TestExam />} />
        <Route path="/tests/feedback/:practiceId/:problemId" element={<FeedBack />} />

        {/* Script 관련 라우트 */}
        <Route path="/scripts" element={<ScriptMain />} />
        <Route path="/scripts/:category" element={<ScriptList />} />
        <Route path="/scripts/:category/:problemId" element={<ScriptDetail />} />
        <Route path="/scripts/:category/:problemId/write" element={<ScriptWrite />} />

        {/* 404 페이지 */}
        <Route path="*" element={<div>페이지를 찾을 수 없습니다.</div>} />
      </Routes>
    </HeaderProvider>
  </BrowserRouter>
  );
}

export default App;
