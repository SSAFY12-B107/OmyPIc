import styles from './TestMain.module.css';
import TestTypeButton from '../../components/test/TestTypeButton';
import AverageGradeChart from '../../components/test/AverageGradeChart';
import RecordItem from '../../components/test/RecordItem';
import axios from 'axios';

import { useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store';
import { testActions } from '../../store/index'


function TestMain() {

    // 비동기 액션 연결 
  const dispatch = useDispatch();

  // 테스트 배포 : 문제 생성 3회 제한

  const { usageCount, maxUsageCount } = useSelector((state: RootState) => state.tests);

   // 생성 횟수 확인
   const canUse = usageCount < maxUsageCount;

  const navigate = useNavigate()

  // 생성 버튼 핸들링-axios 요청
  const handleCreateTest = async (test_type: boolean) => {
    if (canUse) {
      try {
        // API 호출
        const response = await axios.get(`/api/tests/${test_type}`);
        
        // 응답 데이터를 Redux에 저장
        dispatch(testActions.setCurrentTest(response.data));
        
        // 사용 횟수 증가
        dispatch(testActions.incrementUsageCount());
        
        // 페이지 이동
        navigate('/tests/practice');
      } catch (error) {
        console.error('테스트 생성 오류:', error);
        // 에러 처리 로직
      }
    }
  }


  return (
    <div className={styles.container}>
      {/* 테스트 배포 : 3회 응시 횟수 제한 추가 필요 */}
      <main className={styles.main}>
        <section className={styles.section}>
          <h2>시험유형 선택</h2>
          <div className={styles.testTypes}>
            <TestTypeButton 
              onClick={() => handleCreateTest(true)}
              title="실전 모의고사"
              description="실제 시험처럼 연습하기"
              duration="40분"
            />
            <TestTypeButton 
              onClick={() => handleCreateTest(false)}
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