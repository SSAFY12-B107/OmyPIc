// RecordItem.tsx 수정
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import styles from "./RecordItem.module.css";
import { TestHistory, UserHistoryResponse } from "@/hooks/useHistory";

interface RecordItemProps {
  test_pk: string;
  date: string;
}

function RecordItem({ date, test_pk }: RecordItemProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // 리덕스 대신 직접 쿼리 캐시에서 데이터 가져오기
  const userHistoryData = queryClient.getQueryData<UserHistoryResponse>([
    "userHistory",
  ]);

  // 컴포넌트 내에서 현재 test_pk에 해당하는 데이터만 찾기
  const [recordData, setRecordData] = useState<TestHistory | null>(null);

  useEffect(() => {
    if (userHistoryData?.test_history) {
      const currentRecord = userHistoryData.test_history.find(
        (record) => record.id === test_pk
      );

      if (currentRecord) {
        setRecordData(currentRecord);
        console.log("currentRecord", currentRecord);
      }
    }
  }, [userHistoryData, test_pk]);

  const goToDetailHandler = () => {
    console.log(test_pk)
    navigate(`feedback/${test_pk}`);
  };

  // recordData에서 필요한 정보 추출
  const status =
    recordData?.overall_feedback_status === "completed" ? "평가완료" : "미평가";
  const grade = recordData?.test_score?.total_score;
  const scores = {
    description: recordData?.test_score?.comboset_score,
    roleplay: recordData?.test_score?.roleplaying_score,
    impromptu: recordData?.test_score?.unexpected_score,
  };

  useEffect(() => {
    console.log('status',status)
  }, [status])
  // 평가 완료 여부 확인
  const isEvaluating = status === "미평가" || !grade || !scores.description;

  return (
    <div className={styles.container}>
      {/* 나머지 컴포넌트 내용은 유지 */}
      <div className={styles.header}>
        <span className={styles.date}>{date}</span>
        <div className={styles.checkIcon} onClick={goToDetailHandler}>
          <div className={styles.circle}></div>
          <svg
            className={styles.svg}
            width="48"
            height="48"
            viewBox="0 0 48 48"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M18 24H30M30 24L25 19M30 24L25 29"
              stroke="#845ADF"
              strokeWidth="2"
            />
          </svg>
        </div>
      </div>

      {isEvaluating ? (
        <div className={styles.loadingContainer}>
          <div className={styles.loadingSpinner}></div>
          <p className={styles.loadingText}>평가 진행 중...</p>
        </div>
      ) : (
        <>
          <div className={styles.divider}></div>
          <div className={styles.gradeInfo}>
            <span className={styles.gradeLabel}>예상등급</span>
            <span className={styles.grade}>{grade}</span>
          </div>

          <div className={styles.scores}>
            <div className={styles.scoreItem}>
              <span className={styles.scoreLabel}>콤보셋</span>
              <div className={styles.scoreGrade}>{scores.description}</div>
            </div>
            <div className={styles.scoreItem}>
              <span className={styles.scoreLabel}>롤플레잉</span>
              <div className={styles.scoreGrade}>{scores.roleplay}</div>
            </div>
            <div className={styles.scoreItem}>
              <span className={styles.scoreLabel}>돌발질문</span>
              <div className={styles.scoreGrade}>{scores.impromptu}</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default RecordItem;
