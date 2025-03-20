import { Link, useParams } from "react-router-dom";
import ScriptBox from "../../components/script/ScriptBox";
import QuestionBox from "../../components/script/QuestionBox";
import styles from "./ScriptDetail.module.css";
import { useGetProblemDetail } from "../../hooks/useProblems";
import LoadingSpinner from "../../components/common/LoadingSpinner";

type Props = {};

function ScriptDetail({}: Props) {
  // URL 파라미터 가져오기
  const { category, problemId } = useParams<{
    category: string;
    problemId: string;
  }>();

  // 문제 상세 정보 가져오기
  const {
    data: problemDetail,
    isLoading,
    error,
  } = useGetProblemDetail(problemId || "");

  // early return으로 상태 처리
  if (isLoading) {
    return (
      <div className={styles["script-detail-container"]}>
        {/* 공통 헤더 */}
        <span className={styles["category"]}>{category}</span>
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles["script-detail-container"]}>
        {/* 공통 헤더 */}
        <div>문제 정보를 불러오는데 오류가 발생했습니다.</div>
      </div>
    );
  }

  if (!problemDetail) {
    return (
      <div className={styles["script-detail-container"]}>
        {/* 공통 헤더 */}
        <div>문제 정보를 찾을 수 없습니다.</div>
      </div>
    );
  }

  return (
    <div className={styles["script-detail-container"]}>
      {/* 공통 헤더 */}
      <span className={styles["category"]}>{category}</span>

      {/* 질문 */}
      <QuestionBox title="질문" content={problemDetail?.problem.content} />
      {/* 나만의 스크립트 */}
      <ScriptBox userScript={problemDetail?.user_scripts} />

      {/* 나의 모의고사 답변 */}
      <div className={styles["question-box"]}>
        {/* title */}
        <div className={styles["title-box"]}>
          <div className={styles["icon-box"]}>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
            >
              <path
                d="M12 13C11.436 13 10.9617 12.8077 10.577 12.423C10.1923 12.0383 10 11.564 10 11V5C10 4.436 10.1923 3.96167 10.577 3.577C10.9617 3.19233 11.436 3 12 3C12.564 3 13.0383 3.19233 13.423 3.577C13.8077 3.96167 14 4.436 14 5V11C14 11.564 13.8077 12.0383 13.423 12.423C13.0383 12.8077 12.564 13 12 13ZM11.5 20.5V16.983C9.93333 16.839 8.625 16.1983 7.575 15.061C6.525 13.9237 6 12.57 6 11H7C7 12.3833 7.48767 13.5627 8.463 14.538C9.43833 15.5133 10.6173 16.0007 12 16C13.3827 15.9993 14.562 15.5117 15.538 14.537C16.514 13.5623 17.0013 12.3833 17 11H18C18 12.5707 17.475 13.9247 16.425 15.062C15.375 16.1993 14.0667 16.8393 12.5 16.982V20.5H11.5Z"
                fill="#8E8E8E"
              />
            </svg>
          </div>
          <p>나의 모의고사 답변</p>
        </div>

        {/* content */}
        <div className={styles.noteList}>
          {problemDetail?.test_notes?.length > 0 ? (
            problemDetail?.test_notes?.map((note, noteIdx) => (
              <div key={noteIdx} className={styles.noteItem}>
                <p>{note}</p>
              </div>
            ))
          ) : (
            <p className={styles.noContent}>아직 작성된 답변이 없습니다.</p>
          )}
        </div>
      </div>

      <Link to={`/scripts/${category}/${problemId}/write`}>
        <button className={styles["create-btn"]}>스크립트 생성하기</button>
      </Link>
    </div>
  );
}

export default ScriptDetail;
