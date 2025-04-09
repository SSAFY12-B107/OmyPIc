import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import styles from "@/components/common/Header.module.css";
import { useHeader } from "@/contexts/HeaderContext";

// 뒤로가기 시 경고가 필요한 경로 목록
const WARNING_PATHS = ["/tests/practice"];

// 스크립트 작성 페이지에 대한 경고 패턴
const SCRIPT_WRITE_PATTERN = /^\/scripts\/[^\/]+\/[^\/]+\/write$/;

console.log('SCRIPT_WRITE_PATTERN', SCRIPT_WRITE_PATTERN.test(location.pathname))

const Header: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [showWarningModal, setShowWarningModal] = useState<boolean>(false);

  // 헤더 컨텍스트에서 상태 가져오기
  const { 
    title, 
    hideHeader, 
    hideBackButton, 
    customBackAction,
    testEndAction 
  } = useHeader();

  // 현재 경로가 경고가 필요한 경로인지 확인
  const needsWarning =
    WARNING_PATHS.some((path) => location.pathname.includes(path)) ||
    SCRIPT_WRITE_PATTERN.test(location.pathname);

    console.log('needsWarning', needsWarning)

  // 뒤로가기 처리 함수
  const handleBack = () => {
    if (customBackAction) {
      customBackAction();
      return;
    }

    if (needsWarning) {
      setShowWarningModal(true);
    } else {
      navigate(-1);
    }
  };

  // 경고 모달에서 확인 버튼 클릭 시
  const handleConfirmExit = () => {
    setShowWarningModal(false);
    
    if (location.pathname.includes('/tests/practice') && testEndAction) {
      // 테스트 종료 처리 함수 호출
      testEndAction();
    } else {
      // 일반적인 뒤로가기
      navigate(-1);
    }
  };

  // 경고 모달에서 취소 버튼 클릭 시
  const handleCancelExit = () => {
    setShowWarningModal(false);
  };

  // 헤더가 숨겨져 있다면 아무것도 렌더링하지 않음
  if (hideHeader) {
    return null;
  }

  return (
    <>
      <header className={styles.header}>
        <div className={styles.safeArea}>
          <div className={styles.headerContent}>
            {!hideBackButton && (
              <button
                className={styles.backButton}
                onClick={handleBack}
                aria-label="뒤로 가기"
              >
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M19 12H5"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M12 19L5 12L12 5"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            )}
            <h1 className={styles.title}>{title}</h1>
          </div>
        </div>
      </header>

      {showWarningModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <h3>정말 나가시겠습니까?</h3>
            <p>
              {location.pathname.includes("/tests/practice")
                ? "진행 중인 실전 연습이 종료되고 횟수가 차감됩니다."
                : "작성한 내용이 저장되지 않고 모두 사라집니다."}
            </p>
            <div className={styles.modalButtons}>
              <button
                onClick={handleCancelExit}
                className={styles.cancelButton}
              >
                계속하기
              </button>
              <button
                onClick={handleConfirmExit}
                className={styles.confirmButton}
              >
                종료하기
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Header;
