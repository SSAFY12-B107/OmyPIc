import { useCallback } from "react";
import styles from "./LoginButtons.module.css";
import googleLogin from "@/assets/images/google_login.png";

function LoginButtons() {
  // Google 로그인으로 GET 요청을 보내는 함수
  const handleGoogleLogin = useCallback(() => {
    // 브라우저 리다이렉트 사용 (axios가 아님)
    window.location.href = "https://omypic.store/api/auth/google/login";
  }, []);

  return (
    <div className={styles.loginBtnGroup}>
      <img
        src={googleLogin}
        alt="google-login-btn"
        onClick={handleGoogleLogin}
        style={{ cursor: "pointer" }}
      />
    </div>
  );
}

export default LoginButtons;