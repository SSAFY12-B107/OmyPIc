
import styles from "./OveralFeedBack.module.css";

interface OveralFeedbackProps {
  feedback?: string;
}

function OveralFeedback({ 
  feedback = "여행에 대한 기본 정보는 제공했으나, 더 구체적인 경험을 묘사해주세요."
}: OveralFeedbackProps) {
  return (
    <div>
      <div className={styles.feedbackCard}>
        <div className={styles.feedbackHeader}>
          <div className={styles.iconCircle}>
            <div className={styles.personIcon}>👤</div>
          </div>
          <span className={styles.feedbackTitle}>종합 피드백</span>
        </div>
        <p className={styles.feedbackContent}>{feedback}</p>
      </div>
    </div>
  );
}

export default OveralFeedback;