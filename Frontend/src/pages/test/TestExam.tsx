import styles from "./TestExam.module.css";

// 타입 정의
interface TestExamProps {
  initialValue?: number;
  maxValue?: number;
}

function TestExam({ initialValue = 1, maxValue = 15 }: TestExamProps) {
  return (
    <div className={styles.container}>
      <div className={styles.resize}>
        <div className={styles.numBox}>
          <span className={styles.currentNum}>{initialValue}</span>
          <span className={styles.totalNum}> / {maxValue}</span>
        </div>
        <progress
          className={styles.progress}
          value={initialValue}
          max={maxValue}
        ></progress>
        <img className={styles.avatarImg} src="" alt="" />
        <button className={styles.playBtn}>
          <span className={styles.headphoneIcon}>🎧</span>
          다시듣기
        </button>
      </div>

      <div className={styles.answerBox}>
        <div className={styles.setDisplay}>
          <div className={styles.circleIcon}>
            <div className={styles.circle}></div>
            <span className={styles.micIcon}>🎤</span>
          </div>
          <span className={styles.answerText}>내 답변</span>
        </div>
        <div className={styles.animationBox}>
          <img src="/" alt="안녕녕" />
        </div>
      </div>

      <button className={styles.nextButton}>다음</button>
    </div>
  );
}

export default TestExam;
