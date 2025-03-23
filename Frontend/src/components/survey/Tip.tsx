import styles from "./Tip.module.css";
import opigi from "@/assets/images/opigi.png";

interface Props {
  type?: string;
  tipNumber?: number; // 숫자로 관리하기 위한 prop 추가
}

function Tip({ type, tipNumber = 1 }: Props) {
  // 팁 내용 결정
  const getTipText = () => {
    // tipNumber가 제공되면 숫자로 결정, 그렇지 않으면 type으로 결정
    if (tipNumber) {
      switch (tipNumber) {
        case 1:
          return (
            <>
              <strong>'일 경험 없음'</strong>을 선택하면
              <br />
              비즈니스보다 쉬운
              <br />
              일상표현을 할 수 있어요
            </>
          );
        case 2:
          return (
            <>
              <strong>'아니오'</strong>와 <strong>'수강 후 5년 이상 지남'</strong>
              을 선택하면
              <br />
              학업 관련 문제가 출제되지 않아
              <br />
              많은 응시자들이 이 방법을 활용해요.
            </>
          );
        case 3:
          return (
            <>
              <strong>'개인주택이나 아파트에 홀로 거주'</strong>를 선택하면
              <br />
              복잡한 가족 관계를 설명할 필요 없이
              <br />
              많은 응시자들이 전략적으로 선택해요.
            </>
          );
        case 4:
          return (
            <>
              <strong>별 표시된 활동</strong>은
              <br />
              쉽게 설명할 수 있고 구체적인 경험을
              <br />
              떠올리기 좋은 주제예요.
            </>
          );
        case 5:
          return (
            <>
              <strong>별 표시된 취미</strong>는
              <br />
              간단한 단어로도 충분히 설명할 수 있어
              <br />
              대화를 이어가기 좋은 주제예요.
            </>
          );
        case 6:
          return (
            <>
              <strong>별 표시된 운동</strong>은
              <br />
              복잡한 규칙이나 전문 용어 없이도
              <br />
              설명하기 쉬운 주제예요.
            </>
          );
        case 7:
          return (
            <>
              <strong>별 표시된 여행지</strong>는
              <br />
              간단한 표현으로도 경험을 설명하기
              <br />
              쉬워 준비 부담이 적은 주제예요.
            </>
          );
        default:
          return null;
      }
    } else {
      // 기존 type 기반 로직 유지
      switch (type) {
        case "workExperience":
          return (
            <>
              <strong>'일경험 없음'</strong>을 선택하면
              <br />
              비즈니스보다 쉬운
              <br />
              일상표현을 할 수 있어요
            </>
          );
        case "academicBackground":
          return (
            <>
              <strong>'아니오'</strong>와 <strong>'수강 후 5년 이상 지남'</strong>
              을 선택하면
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