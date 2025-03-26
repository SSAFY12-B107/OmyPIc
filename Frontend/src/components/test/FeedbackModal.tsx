import styles from "./FeedbackModal.module.css";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: {
    feedback: {
      paragraph: string;
      spoken_amount: string;
      vocabulary: string;
    };
    score : string;
  } | null;
  isLoading: boolean;
}

const FeedbackModal: React.FC<FeedbackModalProps> = ({
  isOpen,
  onClose,
  data,
  isLoading,
}) => {
  if (!isOpen) return null;

  const [clickType, setClickType] = useState<number>(0);

  // 데이터와 내부 속성의 존재 여부 확인
  const isDataValid =
    data &&
    data.feedback &&
    data.feedback.paragraph &&
    data.feedback.spoken_amount &&
    data.feedback.vocabulary;

  const paragraph = data?.feedback?.paragraph;
  const spokenAmount = data?.feedback?.spoken_amount;
  const vocabulary = data?.feedback?.vocabulary;
  const score = data?.score

  const navigate = useNavigate();

  const handleBttn = (type: number) => {
    setClickType(type);
  };

  // 모달 닫고 테스트 페이지로 이동하는 함수
  const handleCloseAndNavigate = () => {
    onClose(); // 모달 닫기
    navigate("/tests"); // 테스트 페이지로 이동
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        {isLoading || !isDataValid ? (
          <div className={styles.feedbackLoading}>
            <div className={styles.loadingSpinner}></div>
            <p>평가 결과를 불러오는 중입니다...</p>
          </div>
        ) : (
          <div>
            <div className={styles.modalHeader}>
              <h2 className={styles.modalTitle}>피드백이 도착했어요!</h2>
              <div
                className={styles.modalCloseButton}
                onClick={handleCloseAndNavigate}
              >
                <div className={styles.closeIcon}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M16.308 7.333L7.691 15.95M7.691 7.333L16.308 15.95"
                      stroke="#757575"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
              </div>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.gradeInfo}>
                <span className={styles.gradeLabel}>예상등급</span>
                <span className={styles.gradeValue}>{score}</span>
              </div>
              <div className={styles.evaluationCard}>
                <div className={styles.evaluationTags}>
                  <div className={styles.tagGroup}>
                    <div
                      className={`${styles.tag} ${
                        clickType === 0 ? styles.activeTag : ""
                      }`}
                      onClick={() => handleBttn(0)}
                    >
                      문단구성
                    </div>
                    <div
                      className={`${styles.tag} ${
                        clickType === 1 ? styles.activeTag : ""
                      }`}
                      onClick={() => handleBttn(1)}
                    >
                      어휘력
                    </div>
                    <div
                      className={`${styles.tag} ${
                        clickType === 2 ? styles.activeTag : ""
                      }`}
                      onClick={() => handleBttn(2)}
                    >
                      발화량
                    </div>
                  </div>
                </div>
                <p className={styles.feedbackText}>
                  {clickType === 0
                    ? paragraph
                    : clickType === 1
                    ? vocabulary
                    : spokenAmount}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FeedbackModal;
