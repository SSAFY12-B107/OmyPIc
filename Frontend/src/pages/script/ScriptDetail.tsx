import QuestionBox from "../../components/script/QuestionBox";
import ScriptBox from "../../components/script/ScriptBox";
import styles from "./ScriptDetail.module.css";

type Props = {};

function ScriptDetail({}: Props) {
  return (
    <div className={styles["script-detail-container"]}>
      {/* 공통 헤더 */}

      <span className={styles["category"]}>[category]</span>

      {/* 질문 : 아이콘 다르게 */}
      <QuestionBox title="질문" content="질문 내용 넣기" />
      {/* 나만의 스크립트 */}
      <ScriptBox content="생성된 스크립트 내용 넣기" />
      {/* 나의 모의고사 답변 : 아이콘 다르게 */}
      <QuestionBox title="나의 모의고사 답변" content="답변 내용 넣기" />

      <button className={styles["create-btn"]}>스크립트 생성하기</button>
    </div>
  );
}

export default ScriptDetail;
