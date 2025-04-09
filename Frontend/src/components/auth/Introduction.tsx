import styles from "./Introduction.module.css";
import logo from "@/assets/images/logo.png";
import opigi from "@/assets/images/opigi.webp";
import intro1 from "@/assets/images/intro1.webp";
import intro2 from "@/assets/images/intro2.webp";

// 소개 컴포넌트의 타입 정의
export type IntroType = "first" | "second" | "third";

interface Props {
  type: IntroType;
}

function Introduction({ type }: Props) {
  // 각 타입별 컨텐츠 렌더링
  const renderContent = () => {
    switch (type) {
      case "first":
        return (
          <div className={styles.introFirst}>
            <div className={styles.character}>
              <h1 className={styles.logoImg}>
                <img src={logo} alt="logo-img" />
              </h1>
              <img src={opigi} alt="opigi-img" className={styles.opigiImg} />
            </div>

            <div className={styles.textContainer}>
              <p className={styles.mainText}>
                생성형 AI와 함께
                <br />
                <span>단기간</span> 오픽 취득하기
              </p>
            </div>
          </div>
        );

      case "second":
        return (
          <div className={styles.introSecond}>
            <div className={styles.chatContainer}>
              <img src={intro1} alt="intro1-img" />
            </div>

            <div className={styles.textContainer}>
              <p className={styles.mainText}>
                친구처럼 편하게 대화를 나누고,
                <br />
                <span>나만의 스크립트</span>를 만들어보세요
              </p>
              <p className={styles.subText}>
                심층질문을 통해 더욱 탄탄하게 구성할 수 있어요
              </p>
            </div>
          </div>
        );

      case "third":
        return (
          <div className={styles.introThird}>
            <div className={styles.testContainer}>
              <img src={intro2} alt="intro2-img" />
            </div>

            <div className={styles.textContainer}>
              <p className={styles.mainText}>
                실제와 유사한 테스트를 경험하고,
                <br />
                <span>예상 등급</span>을 받을 수 있어요
              </p>
              <p className={styles.subText}>구체적인 피드백을 받을 수 있어요</p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div
      className={`${styles.introComponent} ${
        styles[`intro${type.charAt(0).toUpperCase() + type.slice(1)}`]
      }`}
    >
      {renderContent()}
    </div>
  );
}

export default Introduction;
