import styles from "./DetailFeedBack.module.css";

interface DetailFeedBackProps {
  question?: string;
  answer?: string;
  feedback?: string;
  expectedGrade?: string;
  evaluations?: {
    paragraphStructure: boolean;
    vocabulary: boolean;
    fluency: boolean;
  };
}

function DetailFeedBack({
  question = "Tell me about your home.",
  answer = "I live in apartment.",
  feedback = "여행에 대한 기본 정보는 제공했으나, 더 구체적인 경험을 묘사해주세요.",
  expectedGrade = "IH",
  evaluations = {
    paragraphStructure: true,
    vocabulary: false,
    fluency: false,
  }
}: DetailFeedBackProps) {
  
  
  return (
    <div className={styles.container}>

      <div className={styles.gradeCard}>
        <div className={styles.iconWrapper}>
          <div className={styles.circleIcon}>
            <span className={styles.starIcon}>⭐</span>
          </div>
          <span className={styles.gradeTitle}>예상등급</span>
        </div>
        <div className={styles.gradeBadge}>{expectedGrade}</div>
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

        <div className={styles.evaluationTags}>
          <div className={`${styles.tag} ${evaluations.paragraphStructure ? styles.activeTag : ''}`}>
            문단구성
          </div>
            <div className={`${styles.tag} ${evaluations.vocabulary ? styles.activeTag : ''}`}>
              어휘력
            </div>
            <div className={`${styles.tag} ${evaluations.fluency ? styles.activeTag : ''}`}>
              발화량
            </div>
        </div>

        <p className={styles.feedbackText}>{feedback}</p>
      </div>
    </div>
  );
}

export default DetailFeedBack;