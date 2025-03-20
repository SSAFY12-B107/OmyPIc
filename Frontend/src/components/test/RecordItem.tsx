import styles from "./RecordItem.module.css";

interface RecordItemProps {
  date: string;
  grade: string;
  scores: {
    description: string;
    roleplay: string;
    impromptu: string;
  };
}

function RecordItem({ date, grade, scores }: RecordItemProps) {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
          <span className={styles.date}>{date}</span>
          <div className={styles.checkIcon}>
            <div className={styles.circle}></div>
            <span className={styles.icon}>✓</span>
        </div>
      </div>

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
    </div>
  );
}

export default RecordItem;
