import styles from "./LoginSwitchingPage.module.css";
import NavigationButton from "@/components/common/NavigationButton";
import opigi from "../assets/images/opigi.png";

type Props = {};

function LoginSwitchingPage({}: Props) {
  const handlePrev = () => {
    // 이전 페이지로 이동하는 로직
    console.log("이전 버튼 클릭");
  };

  const handleNext = () => {
    // 다음 페이지로 이동하는 로직
    console.log("다음 버튼 클릭");
  };

  return (
    <div className={styles.loginSwitchingPage}>
      <div className={styles.content}>
        <div className={styles.characterContainer}>
        <img src={opigi} alt="opigi-img" className={styles.opigiImg} />
        </div>

        <div className={styles.textContainer}>
          <p className={styles.message}>
            실제 시험에서는 <span className={styles.boldText}>서베이</span>를 진행해요.
          </p>
          <p className={styles.message}>
            시험과 유사한 환경에서 연습할 수 있게 응답해주세요.
          </p>
        </div>
      </div>

      <div className={styles.navigationContainer}>
        <NavigationButton type="prev" onClick={handlePrev} />
        <NavigationButton type="next" onClick={handleNext} />
      </div>
    </div>
  );
}

export default LoginSwitchingPage;