import { Link } from "react-router-dom";
import QuestionBox from "../../components/script/QuestionBox";
import ScriptBox from "../../components/script/ScriptBox";
import styles from "./ScriptDetail.module.css";

type Props = {};

function ScriptDetail({}: Props) {
  return (
    <div className={styles["script-detail-container"]}>
      {/* 공통 헤더 */}

      <span className={styles["category"]}>[category]</span>

      {/* 질문 */}
      <QuestionBox type="question" title="질문" content="질문 내용 넣기" />
      {/* 나만의 스크립트 */}
      <ScriptBox content="생성된 스크립트 내용 넣기" />
      {/* 나의 모의고사 답변 */}
      <QuestionBox
        type="answer"
        title="나의 모의고사 답변"
        content="답변 내용 넣기"
      />

      {/* 경로 수정 필요 */}
      <Link to={"/scripts/${category}/${problemId}/write"}>
        <button className={styles["create-btn"]}>스크립트 생성하기</button>
      </Link>
    </div>
  );
}

export default ScriptDetail;
