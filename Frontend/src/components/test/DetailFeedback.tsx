import styles from "./DetailFeedBack.module.css";
import { ProblemData } from "../../hooks/useFeedBack";

interface DetailFeedBackProps {
  data: ProblemData | null;
}

function DetailFeedBack({ data }: DetailFeedBackProps) {
  // 피드백 데이터에서 값 추출
  const question = data.problem || "문제 정보가 없습니다.";
  const answer = data.user_response || "답변이 기록되지 않았습니다.";
  const score = data.score || "평가 대기중";

  // 피드백이 없는 경우를 위한 기본값 설정
  const paragraph = data.feedback?.paragraph || "피드백이 아직 제공되지 않았습니다.";
  const vocabulary = data.feedback?.vocabulary || "피드백이 아직 제공되지 않았습니다.";
  const spokenAmount = data.feedback?.spoken_amount || "피드백이 아직 제공되지 않았습니다.";
  

  return (
    <div className={styles.container}>
      <div className={styles.gradeCard}>
        <div className={styles.iconWrapper}>
          <div className={styles.circleIcon}>
            <span className={styles.starIcon}>⭐</span>
          </div>
          <span className={styles.gradeTitle}>예상등급</span>
        </div>
        <div className={styles.gradeBadge}>{}</div>
      </div>

      <div className={styles.feedbackCard}>
        <div className={styles.questionSection}>
          <div className={styles.iconWrapper}>
            <div className={styles.circleIcon}>
              <span className={styles.checkIcon}>✓</span>
            </div>
            <span className={styles.sectionTitle}>문제</span>
          </div>
          <p className={styles.questionText}>{question}</p>
        </div>

        <div className={styles.answerSection}>
          <div className={styles.iconWrapper}>
            <div className={styles.circleIcon}>
              <span className={styles.micIcon}>🎤</span>
            </div>
            <span className={styles.sectionTitle}>내 답변</span>
          </div>
          <div className={styles.answerBox}>
            <p className={styles.answerText}>{answer}</p>
          </div>
        </div>
      </div>

      <div className={styles.evaluationCard}>
        <div className={styles.iconWrapper}>
          <div className={styles.circleIcon}>
            <span className={styles.personIcon}>👤</span>
          </div>
          <span className={styles.sectionTitle}>피드백</span>
        </div>
        <div className={styles.feedbackDetails}>
          <div className={styles.feedbackItem}>
            <h4>문단 구성</h4>
            <p className={styles.feedbackText}>{paragraph}</p>
          </div>
          
          <div className={styles.feedbackItem}>
            <h4>어휘력</h4>
            <p className={styles.feedbackText}>{vocabulary}</p>
          </div>
          
          <div className={styles.feedbackItem}>
            <h4>발화량</h4>
            <p className={styles.feedbackText}>{spokenAmount}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DetailFeedBack;
