import { Link } from "react-router-dom";
import styles from "./ScriptMain.module.css";
import opigi from "../../assets/images/opigi.png";
import Navbar from "../../components/common/Navbar";

type Props = {};

function ScriptMain({}: Props) {
  return (
    <div className={styles["script-main-container"]}>
      {/* 공통 헤더 */}

      <div className={styles.scriptMain}>
        {/* 주제/유형 선택 멘트 */}
        <div className={styles["selection-title"]}>
          <p>
            생성형 AI '오피기'와 함께
            <br />
            무슨 주제/유형으로 대화를 나눌까요?
          </p>
          <img src={opigi} alt="opigi-img" />
        </div>

        {/* 유형 선택 */}
        <div className={styles["category-section"]}>
          <span className={styles["category-title"]}>유형별</span>
          <div className={styles["category-list"]}>
            {/* 빈출 문제 : 경로 수정 필요 */}
            <Link to={"/scripts/${category}"}>
              <div className={styles["category-item"]}>
                <div className={styles["icon-box"]}>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="18"
                    height="14"
                    viewBox="0 0 18 14"
                    fill="none"
                  >
                    <path
                      d="M3.5 10.5H10.5V9.5H3.5V10.5ZM3.5 6.5H14.5V5.5H3.5V6.5ZM1.616 14C1.15533 14 0.771 13.846 0.463 13.538C0.155 13.23 0.000666667 12.8453 0 12.384V1.616C0 1.15533 0.154333 0.771 0.463 0.463C0.771667 0.155 1.15567 0.000666667 1.615 0H6.596L8.596 2H16.385C16.845 2 17.2293 2.15433 17.538 2.463C17.8467 2.77167 18.0007 3.156 18 3.616V12.385C18 12.845 17.846 13.2293 17.538 13.538C17.23 13.8467 16.8457 14.0007 16.385 14H1.616ZM1.616 13H16.385C16.5643 13 16.7117 12.9423 16.827 12.827C16.9423 12.7117 17 12.5643 17 12.385V3.615C17 3.43567 16.9423 3.28833 16.827 3.173C16.7117 3.05767 16.5643 3 16.385 3H8.195L6.195 1H1.615C1.43567 1 1.28833 1.05767 1.173 1.173C1.05767 1.28833 1 1.436 1 1.616V12.385C1 12.5643 1.05767 12.7117 1.173 12.827C1.28833 12.9423 1.436 13 1.616 13Z"
                      fill="#8E8E8E"
                    />
                  </svg>
                </div>
                <p>빈출 문제</p>
              </div>
            </Link>
            {/* 고난도 : 경로 수정 필요 */}
            <Link to={"/scripts/${category}"}>
              <div className={styles["category-item"]}>
                <div className={styles["icon-box"]}>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="18"
                    height="14"
                    viewBox="0 0 18 14"
                    fill="none"
                  >
                    <path
                      d="M3.5 10.5H10.5V9.5H3.5V10.5ZM3.5 6.5H14.5V5.5H3.5V6.5ZM1.616 14C1.15533 14 0.771 13.846 0.463 13.538C0.155 13.23 0.000666667 12.8453 0 12.384V1.616C0 1.15533 0.154333 0.771 0.463 0.463C0.771667 0.155 1.15567 0.000666667 1.615 0H6.596L8.596 2H16.385C16.845 2 17.2293 2.15433 17.538 2.463C17.8467 2.77167 18.0007 3.156 18 3.616V12.385C18 12.845 17.846 13.2293 17.538 13.538C17.23 13.8467 16.8457 14.0007 16.385 14H1.616ZM1.616 13H16.385C16.5643 13 16.7117 12.9423 16.827 12.827C16.9423 12.7117 17 12.5643 17 12.385V3.615C17 3.43567 16.9423 3.28833 16.827 3.173C16.7117 3.05767 16.5643 3 16.385 3H8.195L6.195 1H1.615C1.43567 1 1.28833 1.05767 1.173 1.173C1.05767 1.28833 1 1.436 1 1.616V12.385C1 12.5643 1.05767 12.7117 1.173 12.827C1.28833 12.9423 1.436 13 1.616 13Z"
                      fill="#8E8E8E"
                    />
                  </svg>
                </div>
                <p>고난도 문제</p>
              </div>
            </Link>
          </div>
        </div>

        <hr className={styles["section-divider"]}></hr>

        {/* 주제 선택 */}
        <div className={styles["category-section"]}>
          <span className={styles["category-title"]}>주제별</span>
          <div className={styles["category-list"]}>
            {/* 경로 수정 필요 */}
            <Link to={"/scripts/${category}"}>
              <div className={styles["category-item"]}>
                <div className={styles["icon-box"]}>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="18"
                    height="14"
                    viewBox="0 0 18 14"
                    fill="none"
                  >
                    <path
                      d="M3.5 10.5H10.5V9.5H3.5V10.5ZM3.5 6.5H14.5V5.5H3.5V6.5ZM1.616 14C1.15533 14 0.771 13.846 0.463 13.538C0.155 13.23 0.000666667 12.8453 0 12.384V1.616C0 1.15533 0.154333 0.771 0.463 0.463C0.771667 0.155 1.15567 0.000666667 1.615 0H6.596L8.596 2H16.385C16.845 2 17.2293 2.15433 17.538 2.463C17.8467 2.77167 18.0007 3.156 18 3.616V12.385C18 12.845 17.846 13.2293 17.538 13.538C17.23 13.8467 16.8457 14.0007 16.385 14H1.616ZM1.616 13H16.385C16.5643 13 16.7117 12.9423 16.827 12.827C16.9423 12.7117 17 12.5643 17 12.385V3.615C17 3.43567 16.9423 3.28833 16.827 3.173C16.7117 3.05767 16.5643 3 16.385 3H8.195L6.195 1H1.615C1.43567 1 1.28833 1.05767 1.173 1.173C1.05767 1.28833 1 1.436 1 1.616V12.385C1 12.5643 1.05767 12.7117 1.173 12.827C1.28833 12.9423 1.436 13 1.616 13Z"
                      fill="#8E8E8E"
                    />
                  </svg>
                </div>
                <p>[사진찍기]</p>
              </div>
            </Link>
          </div>
        </div>
      </div>

      {/* 네비게이션 탭바 */}
      <Navbar />
    </div>
  );
}

export default ScriptMain;
