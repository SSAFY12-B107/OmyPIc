import styles from "./ScriptBox.module.css";
import opigi from "../../assets/images/opigi.png";

type Props = {
  content: string;
};

function ScriptBox({ content }: Props) {
  // 스크립트 생성 여부 확인(임시)
  const isGenerating: boolean = true;

  return (
    <div className={styles["script-box"]}>
      {/* header */}
      <div className={styles["script-box-header"]}>
        <div className={styles["title-box"]}>
          <div className={styles["icon-box"]}>{/* 아이콘 */}</div>
          <p>나만의 스크립트</p>
        </div>
        {/* 듣기 버튼 */}
        <div className={styles["listen-btn"]}>
          {/* icon : 스크립트 생성 중일 때 다르게 하기 */}
          <span>[]</span>
          <span>발음 듣기</span>
        </div>
      </div>

      {/* content */}
      <div
        className={`${styles["content-box"]} ${
          isGenerating ? styles["generating"] : styles[""]
        }`}
      >
        {isGenerating ? (
          // 스크립트 생성중인 경우
          <>
            <img src={opigi} alt="opigi-img" />
            <p>스크립트를 생성하고 있어요</p>
          </>
        ) : (
          // 스크립트 생성된 경우
          <p>{content}</p>
        )}
      </div>
    </div>
  );
}

export default ScriptBox;
