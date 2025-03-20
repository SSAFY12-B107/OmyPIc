import { Link } from 'react-router-dom'
import styles from './LoginButtons.module.css'
import naverLogin from '../../assets/images/naver_login.png'
import googleLogin from '../../assets/images/google_login.png'

function LoginButtons() {
  // Google 로그인 처리 함수
  // const handleGoogleLogin = () => {
  //   const GOOGLE_CLIENT_ID = "GOOGLE_CLIENT_ID"; // 구글 클라이언트 ID
  //   const REDIRECT_URI = encodeURIComponent(window.location.origin + "/auth/google/callback");

  //   const googleAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${GOOGLE_CLIENT_ID}&redirect_uri=${REDIRECT_URI}&response_type=code&scope=openid%20profile%20email`;

  //   window.location.href = googleAuthUrl;
  // };

  // 네이버 로그인 처리 함수
  const handleNaverLogin = () => {
    // HTTP로 요청
    fetch('http://localhost:8000/api/auth/naver/login')
      .then(response => response.json())
      .then(data => {
        console.log('받은 인증 URL:', data.auth_url);
        if (data.auth_url) {
          // 받은 state값 저장 (나중에 검증할 필요가 있을 경우)
          if (data.state) {
            localStorage.setItem('naver_oauth_state', data.state);
          }
          // 제공받은 URL로 리다이렉트
          window.location.href = data.auth_url;
        } else {
          console.error('인증 URL이 없습니다.');
        }
      })
      .catch(error => {
        console.error('네이버 로그인 초기화 오류:', error);
      });
  };

  return (
    <div className={styles.loginBtnGroup}>
      <img src={naverLogin} 
           alt="naver-login-btn"
           onClick={handleNaverLogin}
           style={{ cursor: 'pointer' }}
      />
      <img
        src={googleLogin}
        alt="google-login-btn"
      />
    </div>
  )
}

export default LoginButtons