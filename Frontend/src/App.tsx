import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ProfilePage from './pages/auth/ProfilePage'; // 경로 수정
import './App.css';

function App() {
  return (
    <div className="app">
      <BrowserRouter>
        <Routes>
          <Route path="/profile" element={<ProfilePage />} />
          {/* 필요한 다른 경로들을 여기에 추가하세요 */}
          <Route path="/" element={<div className="home-container">
            <h1>어플리케이션에 오신 것을 환영합니다</h1>
            <a href="/profile" className="nav-link">프로필 페이지로 이동</a>
          </div>} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;