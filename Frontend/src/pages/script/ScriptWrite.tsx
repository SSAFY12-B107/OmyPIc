import { useState } from "react";
import QuestionBox from "../../components/script/QuestionBox";
import styles from "./ScriptWrite.module.css";
import opigi from "../../assets/images/opigi.png";
import ScriptModal from "../../components/script/ScriptModal";

type Props = {};

function ScriptWrite({}: Props) {
  const [currentStep, setCurrentStep] = useState<number>(1);  // 현재 단계 상태 관리
  const [showModal, setShowModal] = useState(false);  // 모달 표시 여부를 제어하는 state
  const totalSteps = 3; // 총 단계 수

  // 다음 단계로 이동하는 함수
  // const handleNext = (): void => {
  //   if (currentStep < totalSteps) {
  //     setCurrentStep(currentStep + 1);
  //   }
  //   // 다음 단계 관련 추가 로직
  // };

  // 모달 열기 함수
  // const handleOpenModal = () => {
    
  // };

  // 모달 닫기 함수
  const handleCloseModal = () => {
    setShowModal(false);
  };

  return (
    <div className={styles.scriptWriteContainer}>
      {/* 공통 header */}

      {/* 질문 */}
      <QuestionBox title="질문" content="질문 내용 넣기" />

      {/* 프로그래스 바 */}
      <div className={styles.progressBox}>
        {Array.from({ length: totalSteps }, (_, idx) => (
          <div
            key={idx}
            className={`${styles.progressBar} ${
              idx < currentStep ? styles.active : ""
            }`}
          ></div>
        ))}
      </div>

      {/* ai 채팅 */}
      <div className={styles.chatBox}>
        <div className={`${styles.opigiBox} ${styles.chatTxtBox}`}>
          <div className={styles.imgBox}>
            <img src={opigi} alt="" />
            <p>오피기</p>
          </div>
          <div className={styles.chat}>[질문 내용]</div>
        </div>
        <div className={`${styles.myBox} ${styles.chatTxtBox}`}>
          <textarea
            className={styles.chat}
            placeholder="답변 입력하기"
          ></textarea>
          <div className={styles.imgBox}>
            {/* 사진 바꾸기 */}
            <img src={opigi} alt="" />
            <p>나</p>
          </div>
        </div>
      </div>

      {/* 이전/다음 버튼 */}

      {/* 모달 */}
      {showModal && (
        <ScriptModal
          isGenerating={true}
          onClose={handleCloseModal}
          scriptContent="스크립트 넣기"
        />
      )}
    </div>
  );
}

export default ScriptWrite;
