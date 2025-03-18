import styles from "./TestTypeButton.module.css";

interface TestTypeButtonProps {
  type: "실전" | "속성";
  title: string;
  description: string;
  duration: string;
}

function TestTypeButton({ type, title, description, duration }: TestTypeButtonProps) {
  return (
    <button className={styles["test-type-btn-box"]}>
      <div className={styles["purple-bar"]}></div>
      <div className={styles["content"]}>
        <div className={styles["header"]}>
          <h2>{title}</h2>
          <span className={styles["duration"]}>{duration}</span>
        </div>
        <p className={styles["description"]}>{description}</p>
      </div>
      <div className={styles["icon-container"]}>
        <div className={styles["icon-circle"]}>
          <span className={styles["play-icon"]}>▶</span>
        </div>
      </div>
    </button>
  );
}

export default TestTypeButton;
