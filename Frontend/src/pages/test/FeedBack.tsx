// FeedBack.tsx
import { useState } from "react";
import { useParams } from "react-router-dom";
import styles from "./Feedback.module.css";
import DetailFeedBack from "../../components/test/DetailFeedback";
import OveralFeedBack from "../../components/test/OveralFeedback";
import {
  useFeedback,
  getProblemData,
  getTotalProblems,
} from "../../hooks/useFeedBack";

function TestFeedback() {
  // URL에서 test_pk 파라미터 가져오기
  const { test_pk } = useParams<{ test_pk: string }>();

  // 피드백 데이터 가져오기
  const {
    data: feedbackData,
    isLoading,
    isError,
    error,
  } = useFeedback(test_pk);

  // 총 문제 수 계산
  const totalProblems = getTotalProblems(feedbackData);

  // 현재 선택된 단계를 상태로 관리 (0은 종합, 1-n은 개별 피드백)
  const [currentStep, setCurrentStep] = useState(0);

  // 종합을 포함한 모든 단계 배열 생성
  const steps = [0, ...Array.from({ length: totalProblems }, (_, i) => i + 1)];

  // 단계 버튼 클릭 핸들러
  const handleStepClick = (step: number) => {
    setCurrentStep(step);
  };

  // 현재 선택된 문제 데이터 가져오기
  const currentProblemData =
    currentStep > 0 ? getProblemData(feedbackData, currentStep) : undefined;


  return (
    <div className={styles.container}>
      <div className={styles.stepsContainer}>
        {steps.map((step) => (
          <div
            key={step}
            className={`${styles.stepCircle} ${
              currentStep === step ? styles.activeStep : ""
            }`}
            onClick={() => handleStepClick(step)}
            style={{ cursor: "pointer" }} // 클릭 가능함을 시각적으로 표시
          >
            {step === 0 ? (
              <span
                className={
                  currentStep === 0 ? styles.stepTextActive : styles.stepText
                }
              >
                종합
              </span>
            ) : (
              <span
                className={
                  currentStep === step ? styles.stepTextActive : styles.stepText
                }
              >
                {step}
              </span>
            )}
          </div>
        ))}
      </div>
      {currentStep === 0 ? (
        <OveralFeedBack testFeedback={feedbackData?.test_feedback} />
      ) : (
        currentProblemData ? (
          <DetailFeedBack 
            data={currentProblemData.problem} 

          />
        ) : (
          <div className={styles.emptyContainer}>문제 데이터가 없습니다.</div>
        )
      )}
    </div>
  );
}

export default TestFeedback;


