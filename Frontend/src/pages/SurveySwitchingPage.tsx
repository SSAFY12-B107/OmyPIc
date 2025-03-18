import React from "react";
import styles from "./SurveySwitchingPage.module.css";
import NavigationButton from "../components/common/NavigationButton";
import opigi from "../assets/images/opigi.png";

type Props = {};

function SurveySwitchingPage({}: Props) {
  const handlePrev = () => {
    // 이전 페이지로 이동하는 로직
    console.log("이전 버튼 클릭");
  };

  const handleNext = () => {
    // 다음 페이지로 이동하는 로직
    console.log("다음 버튼 클릭");
  };

  return (
    <div className={styles.surveySwitchingPage}>
      <div className={styles.content}>
        <div className={styles.opigiContainer}>
        <img src={opigi} alt="opigi-img" className={styles.opigiImg} />
        </div>

        <div className={styles.textContainer}>
          <p className={styles.message}>
            해당 설문부터 7번 항목까지는
            <br />
            <span className={styles.boldText}>총 합산 12개 이상</span>의 항목 선택해주세요.
          </p>
        </div>
      </div>

      <div className={styles.navigationContainer}>
        <NavigationButton type="prev" onClick={handlePrev} />
        <NavigationButton type="next" onClick={handleNext} />
      </div>
    </div>
  );
}

export default SurveySwitchingPage;