import './App.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        
        <Route path="/"/>

        {/* Auth 관련 라우트 */}
        {/* <Route path="/auth">
          <Route path="login" element={<Login />} />
          <Route path="survey" element={<Survey />} />
        </Route> */}

        {/* Test 관련 라우트 */}
        {/* <Route path="/test">
          <Route path="exam" element={<Exam />} />
          <Route path="feedback/:examId/:questionId" element={<Feedback />} />
        </Route> */}

        {/* Script 관련 라우트 */}
        {/* <Route path="/script">
          <Route path="list" element={<ScriptList />} />
          <Route path="detail/:questionId" element={<ScriptDetail />} />
          <Route path="write/:questionId" element={<ScriptWrite />} />
        </Route> */}

        {/* 404 페이지 */}
        {/* <Route path="*" element={<div>페이지를 찾을 수 없습니다.</div>} /> */}
      </Routes>
    </BrowserRouter>
  );
}

export default App