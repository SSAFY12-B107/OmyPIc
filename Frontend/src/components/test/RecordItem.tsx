// RecordItem.tsx 완전히 간소화된 버전
import { useNavigate } from "react-router-dom";
import styles from "./RecordItem.module.css";
import { TestHistory } from "@/hooks/useHistory";

interface RecordItemProps {
  record: TestHistory; // record 객체 전체를 props로 받음
  date: string;
}

function RecordItem({ record, date }: RecordItemProps) {
  const navigate = useNavigate();

  // 상세 페이지로 이동
  const goToDetailHandler = () => {
    navigate(`feedback/${record.id}`);
  };

  // 필요한 데이터 추출
  const grade = record.test_score?.total_score;
  const scores = {
    description: record.test_score?.comboset_score,
    roleplay: record.test_score?.roleplaying_score,
    impromptu: record.test_score?.unexpected_score,
  };

  const isLoaded = scores.impromptu && scores.description && scores.roleplay;

  return (
    <div className={styles.container}>
      {isLoaded ? (
        <>
          <div className={styles.header}>
            <span className={styles.date}>{date}</span>
            <button
              className={styles.checkIcon}
              onClick={goToDetailHandler}
            >
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
      ) : (
        <div className={styles.noData}>평가 중..🐧</div>
      )}
    </div>
  );
}

export default RecordItem;
