import styles from "./TestTypeButton.module.css";

interface TestTypeButtonProps {
  title: string;
  description: string;
  onClick: () => void;
  isLoading: boolean;
  duration:string;
}

function TestTypeButton({title, description, onClick, isLoading, duration}: TestTypeButtonProps) {
  return (
    <button className={styles["test-type-btn-box"]} onClick={onClick} disabled={isLoading}>
      <div className={styles["purple-bar"]}></div>
      
      {isLoading ? (
        <div className={styles.loadingText}>맞춤형 테스트 생성중..🐧</div>
      ) : (
        <>
          <div className={styles["content"]}>
            <div className={styles["header"]}>
              <h2>{title}</h2>
              <span className={styles["duration"]}>{duration}</span>
            </div>
            <p className={styles["description"]}>{description}</p>
          </div>
          <div className={styles["icon-container"]}>
            <div className={styles["icon-circle"]}>
              <svg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
                <circle cx="30" cy="30" r="28" fill="#F7F5FF" stroke="#CAC9CD" strokeWidth="1" />
                <circle cx="30" cy="30" r="24" fill="none" stroke="#E6E5E5" strokeWidth="2" />
                <path d="M26 22.5C26 21.5 27 21.8 27.5 22L37.5 29.5C38 30 38 30.5 37.5 31L27.5 38.5C27 39 26 38.8 26 38V22.5Z" fill="#CAC9CD" />
              </svg>
            </div>
          </div>
        </>
      )}
    </button>
  );
}

export default TestTypeButton;