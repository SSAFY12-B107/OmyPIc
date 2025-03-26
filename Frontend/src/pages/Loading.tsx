import styles from './Loading.module.css'
import logo from "../assets/images/logo.png";
import opigi from "../assets/images/opigi.png";

type Props = {};

function Loading({}: Props) {
  return (
    <div className={styles.loading}>
      <div className={styles.character}>
        <h1 className={styles.logoImg}>
          <img src={logo} alt="logo-img" />
        </h1>
        <img src={opigi} alt="opigi-img" className={styles.opigiImg} />
      </div>

      <div className={styles.textContainer}>
        <p className={styles.mainText}>
          생성형 AI와 함께
          <br />
          <span>단기간</span> 오픽 취득하기
        </p>
      </div>
    </div>
  );
}

export default Loading;
