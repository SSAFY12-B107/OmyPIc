import styles from "./DetailFeedback.module.css";
import { ProblemData } from "@/hooks/useFeedBack";
import { useState } from "react";

interface DetailFeedBackProps {
  data: ProblemData | null;
}

function DetailFeedBack({ data }: DetailFeedBackProps) {

  const [clickType, setClickType ]= useState<number>(0)

  const handleBttn = (type: number) => {
    setClickType(type)
    
    
  }
  // 피드백 데이터에서 값 추출
  const question = data?.problem || "문제 정보가 없습니다.";
  const answer = data?.user_response || "답변이 기록되지 않았습니다.";
  const score = data?.score || "평가 대기중";

  // 피드백이 없는 경우를 위한 기본값 설정
  const paragraph = data?.feedback?.paragraph || "피드백이 아직 제공되지 않았습니다.";
  const vocabulary = data?.feedback?.vocabulary || "피드백이 아직 제공되지 않았습니다.";
  const spokenAmount = data?.feedback?.spoken_amount || "피드백이 아직 제공되지 않았습니다.";
  

  return (
    <div className={styles.container}>
      <div className={styles.gradeCard}>
        <div className={styles.iconWrapper}>
          <div className={styles.circleIcon}>
            <span className={styles.starIcon}>⭐</span>
          </div>
          <span className={styles.gradeTitle}>예상등급</span>
        </div>
        <div className={styles.gradeBadge}>{score}</div>
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
          <div className={styles.tagGroup}>
            <div
              className={`${styles.tag} ${clickType === 0 ? styles.activeTag : ""}`}
              onClick={() => handleBttn(0)}
            >
              문단구성
            </div>
            <div
              className={`${styles.tag} ${clickType === 1 ? styles.activeTag : ""}`}
              onClick={() => handleBttn(1)}
            >
              어휘력
            </div>
            <div
              className={`${styles.tag} ${clickType === 2 ? styles.activeTag : ""}`}
              onClick={() => handleBttn(2)}
            >
              발화량
            </div>
          </div>
        </div>
        <p className={styles.feedbackText}>
          {clickType === 0 ? paragraph : clickType === 1 ? vocabulary : spokenAmount}
        </p>
      </div>
    </div>
  );
}

export default DetailFeedBack;
