import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
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

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />

        {/* Auth 관련 라우트 */}
        <Route path="/auth/login" element={<Login />} />
        <Route path="/auth/survey" element={<Survey />} />
        <Route path="/auth/profile" element={<Profile />} />

        {/* Test 관련 라우트 */}
        <Route path="/test" element={<TestMain />} />
        <Route path="/test/exam" element={<TestExam />} />
        <Route path="/test/feedback/:examId/:questionId" element={<FeedBack />} />

        {/* Script 관련 라우트 */}
        <Route path="/script" element={<ScriptMain />} />
        <Route path="/script/list" element={<ScriptList />} />
        <Route path="/script/detail/:questionId" element={<ScriptDetail />} />
        <Route path="/script/write/:questionId" element={<ScriptWrite />} />

        {/* 404 페이지 */}
        <Route path="*" element={<div>페이지를 찾을 수 없습니다.</div>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;