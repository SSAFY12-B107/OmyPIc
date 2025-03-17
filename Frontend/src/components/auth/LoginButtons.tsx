import { Link } from 'react-router-dom'
import styles from './LoginButtons.module.css'
import kakaoLogin from '../../assets/images/kakao_login.png'
import googleLogin from '../../assets/images/google_login.png'

type Props = {}

function LoginButtons({}: Props) {
  return (
    <div className={styles.loginBtnGroup}>
      <img src={kakaoLogin} alt="kakao-login-btn" />
      <img src={googleLogin} alt="google-login-btn" />
    </div>
  )
}

export default LoginButtons