// FeedBack.tsx
import { useState } from "react";
import styles from "./Feedback.module.css";
import DetailFeedBack from "../../components/test/DetailFeedback";
import OveralFeedBack from "../../components/test/OveralFeedback";

interface TestFeedbackProps {
  totalSteps?: number;
  feedback?: string;
}

function TestFeedback({ 
  totalSteps = 7,
  feedback
}: TestFeedbackProps) {
  // 현재 선택된 단계를 상태로 관리 (0은 종합, 1-7은 개별 피드백)
  const [currentStep, setCurrentStep] = useState(0);
  
  // 종합을 포함한 모든 단계 배열 생성
  const steps = [0, ...Array.from({ length: totalSteps }, (_, i) => i + 1)];
  
  // 단계 버튼 클릭 핸들러
  const handleStepClick = (step: number) => {
    setCurrentStep(step);
  };

  return (
    <div className={styles.container}>
      <div className={styles.stepsContainer}>
        {steps.map((step) => (
          <div 
            key={step} 
            className={`${styles.stepCircle} ${currentStep === step ? styles.activeStep : ''}`}
            onClick={() => handleStepClick(step)}
            style={{ cursor: 'pointer' }} // 클릭 가능함을 시각적으로 표시
          >
            {step === 0 ? (
              <span className={currentStep === 0 ? styles.stepTextActive : styles.stepText}>종합</span>
            ) : (
              <span className={currentStep === step ? styles.stepTextActive : styles.stepText}>{step}</span>
            )}
          </div>
        ))}
      </div>
      
      {currentStep === 0 ? (
        <OveralFeedBack feedback={feedback} />
      ) : (
        <DetailFeedBack 
          question={`Question for step ${currentStep}`} 
          answer={`Answer for step ${currentStep}`}
          feedback={`Feedback for step ${currentStep}`}
          expectedGrade="IH"
          evaluations={{
            paragraphStructure: true,
            vocabulary: false,
            fluency: false,
          }}
        />
      )}
    </div>
  );
}

export default TestFeedback;