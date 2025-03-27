import styles from "./LoginButtons.module.css";
// import naverLogin from "@/assets/images/naver_login.png";
import googleLogin from "@/assets/images/google_login.png";

function LoginButtons() {
  // Google 로그인 처리 함수
  const handleGoogleLogin = () => {
    // 서버 요청을 위한 옵션 설정
    // 서버 요청을 위한 옵션 설정
    const requestOptions: RequestInit = {
      method: "GET",
      credentials: "include" as RequestCredentials, // 타입 지정
      headers: {
        "Content-Type": "application/json",
      },
      mode: "cors" as RequestMode, // 타입 지정
    };

    // HTTP로 요청
    fetch("http://omypic.store/api/auth/google/login", requestOptions)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        console.log("받은 인증 URL:", data.auth_url);
        if (data.auth_url) {
          // 받은 state값 저장 (나중에 검증할 필요가 있을 경우)
          if (data.state) {
            localStorage.setItem("google_oauth_state", data.state);
          }
          // 제공받은 URL로 리다이렉트
          window.location.href = data.auth_url;
        } else {
          console.error("인증 URL이 없습니다.");
        }
      })
      .catch((error) => {
        console.error("구글 로그인 초기화 오류:", error);
        // 오류 발생 시 직접 리다이렉트 시도 (백업 방법)
        window.location.href = "http://omypic.store/api/auth/google/login";
      });
  };

  // // 네이버 로그인 처리 함수
  // const handleNaverLogin = () => {
  //   // HTTP로 요청
  //   fetch("http://localhost:8000/api/auth/naver/login")
  //     .then((response) => response.json())
  //     .then((data) => {
  //       console.log("받은 인증 URL:", data.auth_url);
  //       if (data.auth_url) {
  //         // 받은 state값 저장 (나중에 검증할 필요가 있을 경우)
  //         if (data.state) {
  //           localStorage.setItem("naver_oauth_state", data.state);
  //         }
  //         // 제공받은 URL로 리다이렉트
  //         window.location.href = data.auth_url;
  //       } else {
  //         console.error("인증 URL이 없습니다.");
  //       }
  //     })
  //     .catch((error) => {
  //       console.error("네이버 로그인 초기화 오류:", error);
  //     });
  // };

  return (
    <div className={styles.loginBtnGroup}>
      {/* <img
        src={naverLogin}
        alt="naver-login-btn"
        onClick={handleNaverLogin}
        style={{ cursor: "pointer" }}
      /> */}
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
