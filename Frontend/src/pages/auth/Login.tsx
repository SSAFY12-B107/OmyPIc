import { useState, useEffect } from "react";
import Introduction from "@/components/auth/Introduction";
import LoginButtons from "@/components/auth/LoginButtons";
import styles from "./Login.module.css";

type Props = {};

function Login({}: Props) {
  const [currentStep, setCurrentStep] = useState(0);
  const totalSteps = 3;

  // 자동 페이지 전환 로직 - 마지막 페이지에서 첫 페이지로 순환
  useEffect(() => {
    const timer = setTimeout(() => {
      // 마지막 페이지라면 첫 페이지로, 아니면 다음 페이지로
      setCurrentStep((prev) => (prev >= totalSteps - 1 ? 0 : prev + 1));
    }, 2500); // 2.5초 후 다음 페이지로

    return () => clearTimeout(timer);
  }, [currentStep, totalSteps]);

  return (
    <div className={styles.loginContainer}>
      {/* 페이지 인디케이터 */}
      <div className={styles.indicatorContainer}>
        {Array.from({ length: totalSteps }).map((_, index) => (
          <button
            key={index}
            className={`${styles.indicator} ${
              index === currentStep ? styles.active : styles.inactive
            }`}
            aria-label={`페이지 ${index + 1} ${
              index === currentStep ? "(현재 페이지)" : ""
            }`}
            type="button"
          />
        ))}
      </div>

      <div className={styles.contentContainer}>
        {currentStep === 0 && <Introduction type="first" />}
        {currentStep === 1 && <Introduction type="second" />}
        {currentStep === 2 && <Introduction type="third" />}
      </div>

      <LoginButtons />
    </div>
  );
}

export default Login;
