// FeedBack.tsx
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import styles from "./Feedback.module.css";
import DetailFeedBack from "@/components/test/DetailFeedback";
import OveralFeedBack from "@/components/test/OveralFeedback";
import {
  useFeedback,
  getProblemData,
  getTotalProblems,
} from "@/hooks/useFeedBack";
import apiClient from "@/api/apiClient";

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

  console.log("error", error);
  console.log("feedbackData", feedbackData);
  console.log("test_pk", test_pk);

  // 현재 선택된 단계를 상태로 관리 (0은 종합, 1-n은 개별 피드백)
  const [currentStep, setCurrentStep] = useState<number>(0);

  // 실전모의고사(15문제)인 경우 현재 표시할 세트 (1: 문제 1-7, 2: 문제 8-15)
  const [currentSet, setCurrentSet] = useState<number>(1);

  // 데이터가 로드된 후에만 계산
  const totalProblems = getTotalProblems(feedbackData);

  // 테스트 타입 확인 (true: 실전모의고사 15문제, false: 적성고사 7문제)
  const isFullTest = feedbackData?.test_type || false;

  // 현재 선택된 문제 데이터 가져오기
  const currentProblemData =
    currentStep > 0 ? getProblemData(feedbackData, currentStep) : undefined;

  // 현재 세트에 따라 표시할 단계 배열 생성
  const getVisibleSteps = () => {
    // 기본은 종합 버튼
    const steps = currentSet == 1 ? [0] : [];

    if (!feedbackData || !feedbackData.problem_data) return steps;

    // 실전모의고사인 경우 (15문제)
    if (isFullTest) {
      // 현재 세트에 따라 표시할 문제 범위 결정
      const startProblem = currentSet === 1 ? 1 : 8;
      const endProblem = currentSet === 1 ? 7 : Math.min(15, totalProblems);

      // 해당 범위의 문제만 추가
      for (let i = startProblem; i <= endProblem; i++) {
        if (feedbackData.problem_data[i.toString()]) {
          steps.push(i);
        }
      }
    }
    // 적성고사인 경우 (7문제)
    else {
      for (let i = 1; i <= totalProblems; i++) {
        if (feedbackData.problem_data[i.toString()]) {
          steps.push(i);
        }
      }
    }

    return steps;
  };

  // 현재 표시할 단계 배열
  const visibleSteps = getVisibleSteps();

  // 페이지네이션 버튼 표시 여부
  const showPrevButton = isFullTest && currentSet > 1;
  const showNextButton = isFullTest && currentSet === 1 && totalProblems > 7;

  console.log("feedbackData", feedbackData);
  console.log("currentProblemData", currentProblemData);

  // 단계 버튼 클릭 핸들러
  const handleStepClick = (step: number) => {
    setCurrentStep(step);
  };

  // 이전 세트로 이동
  const handlePrevSet = () => {
    if (isFullTest && currentSet > 1) {
      setCurrentSet(currentSet - 1);
      // 현재 선택된 문제가 새 세트에 없으면 종합으로 이동
      if (currentStep >= 8) {
        setCurrentStep(0);
      }
    }
  };

  // 다음 세트로 이동
  const handleNextSet = () => {
    if (isFullTest && currentSet === 1 && totalProblems > 7) {
      setCurrentSet(currentSet + 1);
      // 현재 선택된 문제가 새 세트에 없으면 종합으로 이동
      if (currentStep > 0 && currentStep <= 7) {
        setCurrentStep(0);
      }
    }
  };

  return (
    <div className={styles.container}>
      {/* 단계 버튼 */}
      <div className={styles.stepsContainer}>
        {/* 이전 세트 버튼 */}
        {showPrevButton && (
          <button className={styles.stepCircle} onClick={handlePrevSet}>
            <svg
              className={styles.svg}
              width="48"
              height="48"
              viewBox="0 0 48 48"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M30 24H18M18 24L23 19M18 24L23 29"
                stroke="#845ADF"
                strokeWidth="2"
              />
            </svg>
          </button>
        )}

        {visibleSteps.map((step) => (
          <div
            key={step}
            className={`${styles.stepCircle} ${
              currentStep === step ? styles.activeStep : ""
            }`}
            onClick={() => handleStepClick(step)}
            style={{ cursor: "pointer" }}
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
        {/* 다음 세트 버튼 */}
        {showNextButton && (
          <button className={styles.stepCircle} onClick={handleNextSet}>
            <svg
              className={styles.svg}
              width="48"
              height="48"
              viewBox="0 0 48 48"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M18 24H30M30 24L25 19M30 24L25 29"
                stroke="#845ADF"
                strokeWidth="2"
              />
            </svg>
          </button>
        )}
      </div>

      {currentStep === 0 ? (
        <OveralFeedBack testFeedback={feedbackData?.test_feedback} />
      ) : currentProblemData ? (
        <DetailFeedBack data={currentProblemData} />
      ) : (
        <div className={styles.emptyContainer}>문제 데이터가 없습니다.</div>
      )}
    </div>
  );
}

export default TestFeedback;
