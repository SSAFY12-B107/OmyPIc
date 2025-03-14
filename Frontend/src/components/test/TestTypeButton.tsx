import styles from "./TestTypeButton.module.css";

function TestTypeButton() {
  return (
    <div>
      <div>
        <button className={styles["test-type-btn-box"]}>
          <div className={styles['purple-bar']}></div>
          <div className={styles["set-group-container"]}>
            <div className={styles["text-group"]}>
              <h1 className={styles["test-type-btn-text"]}>실전 모의고사</h1>
              <span className={styles["time-display"]}>40분</span>
            </div>
            <p className={styles["introduction-text"]}>
              실제 시험처럼 연습하기
            </p>
          </div>
          <div className={styles["set-group-container2"]}>
            <div className={styles["back-circle"]}>ㅇㅇ</div>
          </div>
        </button>
      </div>
    </div>
  );
}

export default TestTypeButton;
