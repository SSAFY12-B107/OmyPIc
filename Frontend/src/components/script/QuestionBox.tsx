import { Link } from "react-router-dom";
import styles from "./QuestionBox.module.css";

type Props = {
  title: string;
  content: string;
};

function QuestionBox({ title, content }: Props) {
  return (
    <div className={styles["question-box"]}>
      {/* title */}
      <div className={styles["title-box"]}>
        <div className={styles["icon-box"]}>{/* 아이콘 */}</div>
        <p>{title}</p>
      </div>

      {/* content */}
      {/* 경로 수정 필요 */}
      <Link to={"/script/detail"}>
        <div className={styles["content-box"]}>
          <p>{content}</p>
        </div>
      </Link>
    </div>
  );
}

export default QuestionBox;
