import styles from "./RecordItem.module.css";
import { useNavigate } from "react-router-dom";

interface RecordItemProps {
  date: string;
  grade: string;
  status: string;
  scores: {
    description: string;
    roleplay: string;
    impromptu: string;
  };
  test_pk: string;
}

function RecordItem({ date, grade, status, scores, test_pk }: RecordItemProps) {
  const navigate = useNavigate();

  const goToDetailHandler = () => {
    navigate(`feedback/${test_pk}`);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.date}>{date}</span>
        <div className={styles.checkIcon} onClick={goToDetailHandler}>
          <div className={styles.circle}></div>
          <span className={styles.icon}>✓</span>
        </div>
      </div>

      {status === '미평가' ? (
        <div className={styles.loadingContainer}>
          <div className={styles.loadingSpinner}></div>
          <p className={styles.loadingText}>평가 진행 중...</p>
        </div>
      ) : (
        <>
          <div className={styles.divider}></div>
          <div className={styles.gradeInfo}>
            <span className={styles.gradeLabel}>예상등급</span>
            <span className={styles.grade}>{grade}</span>
          </div>

          <div className={styles.scores}>
            <div className={styles.scoreItem}>
              <span className={styles.scoreLabel}>콤보셋</span>
              <div className={styles.scoreGrade}>{scores.description}</div>
            </div>
            <div className={styles.scoreItem}>
              <span className={styles.scoreLabel}>롤플레잉</span>
              <div className={styles.scoreGrade}>{scores.roleplay}</div>
            </div>
            <div className={styles.scoreItem}>
              <span className={styles.scoreLabel}>돌발질문</span>
              <div className={styles.scoreGrade}>{scores.impromptu}</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default RecordItem;