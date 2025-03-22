import styles from './TestMain.module.css';
import TestTypeButton from '@/components/test/TestTypeButton';
import AverageGradeChart from '@/components/test/AverageGradeChart';
import RecordItem from '@/components/test/RecordItem';

function TestMain() {
  return (
    <div className={styles.container}>

      <main className={styles.main}>
        <section className={styles.section}>
          <h2>시험유형 선택</h2>
          <div className={styles.testTypes}>
            <TestTypeButton 
              type="실전"
              title="실전 모의고사"
              description="실제 시험처럼 연습하기"
              duration="40분"
            />
            <TestTypeButton 
              type="속성"
              title="속성 모의고사"
              description="바쁜 사람들을 위한 스몰 테스트"
              duration="20분"
            />
          </div>
        </section>

        <section className={styles.section}>
          <h2>유형별 나의 평균 등급</h2>
          <AverageGradeChart />
        </section>

        <section className={styles.section}>
          <h2>모의고사 기록</h2>
          <div className={styles.records}>
            <RecordItem 
              date="2025년 3월 8일"
              grade="IH"
              scores={{
                description: "IH",
                roleplay: "IH",
                impromptu: "IH"
              }}
            />
            <RecordItem 
              date="2025년 3월 6일"
              grade="IH"
              scores={{
                description: "IH",
                roleplay: "IM2",
                impromptu: "IM3"
              }}
            />
            <RecordItem 
              date="2025년 2월 28일"
              grade="IH"
              scores={{
                description: "IH",
                roleplay: "IM2",
                impromptu: "IM3"
              }}
            />
          </div>
        </section>
      </main>

    </div>
  );
}

export default TestMain;