import React from "react";
import styles from "./Tip.module.css";
import opigi from "../../assets/images/opigi.png";

// Tip 타입 정의
export type TipType = "workExperience" | "livingAlone" | "academicBackground";

interface Props {
  type: TipType;
}

function Tip({ type }: Props) {
  // 각 타입별 텍스트 컨텐츠 정의
  const getTipText = () => {
    switch (type) {
      case "workExperience":
        return (
          <>
            <strong>'일경험 없음'</strong>을 선택하면
            <br />
            비즈니스보다 쉬운 일상표현을 할 수 있어요
          </>
        );
      case "academicBackground":
            return (
              <>
                <strong>'아니오'</strong>와 <strong>'수강 후 5년 이상 지남'</strong>을 선택하면
                <br />
                학업 관련 문제가 출제되지 않아
                <br />
                많은 응시자들이 이 방법을 활용해요.
              </>
            );

      case "livingAlone":
        return (
          <>
            <strong>'개인주택이나 아파트에 홀로 거주'</strong>를 선택하면
            <br />
            복잡한 가족 관계를 설명할 필요 없이
            <br />
            많은 응시자들이 전략적으로 선택해요.
          </>
        );
      default:
        return null;
    }
  };

  return (
    <div className={styles.tipContainer}>
      <div className={styles.tipHeader}>
        <div className={styles.tipLabel}>
          <span>Tip</span>
        </div>
        <div className={styles.starIcon}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
              <path
                d="M50,10 C52,10 53.5,11 54.5,13 L65,33 C65.5,34 66.5,35 68,35.2 L90,38 C92,38.5 93.5,40 94,42 C94.5,44 93.5,46 92,47.5 L76,63 C75,64 74.5,65.5 75,67 L79,89 C79.5,91 78.5,93 77,94.5 C75.5,95.5 73.5,96 71.5,95 L52,85 C50.5,84.5 49,84.5 47.5,85 L28,95 C26,96 24,95.5 22.5,94.5 C21,93 20,91 20.5,89 L24.5,67 C25,65.5 24.5,64 23.5,63 L8,47.5 C6.5,46 5.5,44 6,42 C6.5,40 8,38.5 10,38 L32,35.2 C33.5,35 34.5,34 35,33 L45.5,13 C46.5,11 48,10 50,10 Z"
                fill="#C09EFF"
                stroke="none"
              />
            </svg>
        </div>
      </div>
      <div className={styles.tipContent}>
        <p className={styles.tipText}>{getTipText()}</p>
      </div>
      <div className={styles.characterContainer}>
        <img src={opigi} alt="오피기" className={styles.character} />
      </div>
    </div>
  );
}

export default Tip;