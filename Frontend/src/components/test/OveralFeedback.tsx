
import styles from "./OveralFeedBack.module.css";
import { MultipleFeedback } from "../../hooks/useFeedBack";


interface OveralFeedbackProps {
  testFeedback?: MultipleFeedback | null;
}

function OveralFeedback({ testFeedback }: OveralFeedbackProps) {
  if (!testFeedback) {
    return <div className={styles.noFeedback}>종합 피드백이 아직 제공되지 않았습니다.</div>;
  }

  return (
    <div>
      <div className={styles.feedbackCard}>
        <div className={styles.feedbackHeader}>
          <div className={styles.iconCircle}>
            <div className={styles.personIcon}>👤</div>
          </div>
          <span className={styles.feedbackTitle}>종합 피드백</span>
        </div>
        <p className={styles.feedbackContent}>{testFeedback.total_feedback}</p>
      </div>
    </div>
  );
}

export default OveralFeedback;