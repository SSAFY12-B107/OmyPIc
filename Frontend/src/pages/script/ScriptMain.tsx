import { Link } from "react-router-dom";
import styles from "./ScriptMain.module.css";
import opigi from "../../assets/images/opigi.png";

type Props = {};

function ScriptMain({}: Props) {
  return (
    <div className={styles["script-main"]}>
      {/* 공통 헤더 */}

      {/* 주제/유형 선택 멘트 */}
      <div className={styles["selection-title"]}>
        <p>
          생성형 AI '오피기'와 함께
          <br />
          무슨 주제/유형으로 대화를 나눌까요?
        </p>
        <img src={opigi} alt="opigi-img" />
      </div>

      {/* 주제 선택 */}
      <div className={styles["category-section"]}>
        <span className={styles["category-title"]}>주제별</span>
        <div className={styles["category-list"]}>
          {/* 경로 수정 필요? */}
          <Link to={"/script/list"}>
            <div className={styles["category-item"]}>
              <div className={styles["icon-box"]}>
                {/* 아이콘 */}
                []
              </div>
              <p>[사진찍기]</p>
            </div>
          </Link>
        </div>
      </div>

      <hr className={styles["section-divider"]}></hr>

      {/* 유형 선택 */}
      <div className={styles["category-section"]}>
        <span className={styles["category-title"]}>유형별</span>
        <div className={styles["category-list"]}>
          {/* 경로 수정 필요? */}
          <Link to={"/script/list"}>
            <div className={styles["category-item"]}>
              <div className={styles["icon-box"]}>
                {/* 아이콘 */}
                []
              </div>
              <p>고득점 Kit</p>
            </div>
          </Link>
        </div>
      </div>

      {/* navbar */}
    </div>
  );
}

export default ScriptMain;
