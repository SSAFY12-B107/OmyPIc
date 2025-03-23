import React from 'react';
import styles from './Switch.module.css';
import NavigationButton from "@/components/common/NavigationButton";
import opigi from "../../assets/images/opigi.png";

type Props = {
  onPrev?: () => void;
  onNext?: () => void;
  step?: number; // 현재 단계 번호
  pageId?: number; // 페이지 ID
};

function Switch({ onPrev, onNext, step = 0, pageId = 0 }: Props) {
  const handlePrev = () => {
    if (onPrev) {
      onPrev();
    }
  };

  const handleNext = () => {
    if (onNext) {
      onNext();
    }
  };

  const renderMessage = () => {
    console.log("Switch 컴포넌트 렌더링. step:", step, "pageId:", pageId);
    
    // 첫 번째 메시지 (0번째 단계)
    if (step === 0) {
      return (
        <div className={styles.textContainer}>
          <p className={styles.message}>
            실제 시험에서는 <span className={styles.boldText}>서베이</span>를 진행해요.
          </p>
          <p className={styles.message}>
            시험과 유사한 환경에서 연습할 수 있게 응답해주세요.
          </p>
        </div>
      );
    }
    // 다중 선택 안내 메시지 (여가 활동 시작 전)
    // pageId 뿐만 아니라 step도 확인
    else if (pageId === 4 || step === 4) {
      return (
        <div className={styles.textContainer}>
          <p className={styles.message}>
            해당 설문부터 7번 항목까지는
            <br />
            <span className={styles.boldText}>총 합산 12개 이상</span>의 항목 선택해주세요.
          </p>
        </div>
      );
    }
    // 기본 메시지
    else {
      return (
        <div className={styles.textContainer}>
          <p className={styles.message}>
            다음 설문을 진행해주세요.
          </p>
        </div>
      );
    }
  };

  return (
    <div className={styles.switchingPage}>
      <div className={styles.content}>
        <div className={styles.characterContainer}>
          <img src={opigi} alt="opigi-img" className={styles.opigiImg} />
        </div>

        {renderMessage()}
      </div>

      <div className={styles.navigationContainer}>
        <NavigationButton type="prev" onClick={handlePrev} />
        <NavigationButton type="next" onClick={handleNext} />
      </div>
    </div>
  );
}

export default Switch;