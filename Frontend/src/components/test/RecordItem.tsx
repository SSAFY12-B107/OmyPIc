import { useNavigate } from "react-router-dom";
import styles from "./RecordItem.module.css";
import { TestHistory } from "@/hooks/useHistory";

interface RecordItemProps {
  record: TestHistory; // record 객체 전체를 props로 받음
  date: string;
}

function RecordItem({ record, date }: RecordItemProps) {
  const navigate = useNavigate();
  // console.log("record.test_type",record.test_type)

  // 상세 페이지로 이동
  const goToDetailHandler = () => {
    navigate(`feedback/${record.id}`);
  };

  // 테스트 타입 매핑 함수
  const getTestTypeName = (testType: number | undefined): string => {
    switch (testType) {
      case 1:
        return "실전 연습";
      case 3:
        return "콤보셋";
      case 4:
        return "롤플레잉";
      case 5:
        return "돌발질문";
      default:
        return "-";
    }
  };

  // 필요한 데이터 추출
  const grade = record.test_score?.total_score;
  const testType = record?.test_type;
  const isFullTest = testType === 1;
  const categoryTest = testType === 3 || testType === 4 || testType === 5;

  // 피드백 완료 상태 확인
  const feedbackCompleted = record.overall_feedback_status === "completed";

  console.log("레코드 아이템 testType", testType);
  console.log("실제 testType 타입:", typeof record.test_type);

  console.log("피드백 상태:", record.overall_feedback_status);
  console.log("테스트 점수:", record.test_score);
  console.log("isFullTest",isFullTest)

  // 점수 설정
  const scores = {
    description:
      ((isFullTest || categoryTest) && record.test_score?.comboset_score) ||
      "-",
    roleplay:
      ((isFullTest || categoryTest) && record.test_score?.roleplaying_score) ||
      "-",
    impromptu:
      ((isFullTest || categoryTest) && record.test_score?.unexpected_score) ||
      "-",
  };

  // 로딩 상태 확인 - 조건 단순화
  const isLoaded = feedbackCompleted; // 피드백 완료 상태만으로 판단

  console.log("isLoaded", isLoaded);
  console.log("scores", scores);

  const testTypeName = getTestTypeName(testType);

  return (
    <div
      className={`${styles.container} ${!isLoaded ? styles.evaluating : ""}`}
    >
      {isLoaded ? (
        <>
          <div className={styles.header}>
            <span className={styles.date}>{date}</span>
            <button className={styles.checkIcon} onClick={goToDetailHandler}>
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
            </button>
          </div>
          <div className={styles.divider}></div>
          <div className={styles.gradeInfo}>
            <div>
              <span className={styles.gradeLabel}>예상등급</span>
              <span className={styles.grade}> {grade}</span>
            </div>
            <span className={styles.testType}>{testTypeName}</span>
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
      ) : (
        <div className={styles.noData}>평가 중..🐧</div>
      )}
    </div>
  );
}

export default RecordItem;
