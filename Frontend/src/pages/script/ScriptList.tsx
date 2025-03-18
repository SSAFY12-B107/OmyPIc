import { Link } from "react-router-dom";
import styles from "./ScriptList.module.css";
import opigi from "../../assets/images/opigi.png";
import QuestionBox from "../../components/script/QuestionBox";

type Props = {};

function ScriptList({}: Props) {
  return (
    <div className={styles["script-list-container"]}>
      {/* 공통 헤더 */}

      {/* 질문 선택 멘트 */}
      <div className={styles["selection-title"]}>
        <p>
          <span>[]</span>을 선택하셨네요!
          <br />
          무슨 질문으로 대화를 나눌까요?
        </p>
        <img src={opigi} alt="opigi-img" />
      </div>

      {/* 질문 리스트 */}
      <div className={styles["question-list"]}>
        <Link to={"scripts/${category}/${problemId}"}>
          {/* title, content 넣어주기 */}
          <QuestionBox type="question" title="질문 제목" content="질문 내용" />
        </Link>
      </div>
    </div>
  );
}

export default ScriptList;
