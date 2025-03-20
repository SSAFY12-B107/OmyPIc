import styles from './TestMain.module.css';
import TestTypeButton from '../../components/test/TestTypeButton';
import AverageGradeChart from '../../components/test/AverageGradeChart';
import RecordItem from '../../components/test/RecordItem';
import apiClient from '../../api/apiClient';

import { useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store';
import { testActions } from '../../store/index'
import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useUserHistory } from '../../hooks/useHistory';



function TestMain() {

  // 히스토리 조회 
  const { user_pk } = useParams<{ user_pk: string  }>();

  // // 또는 Redux에서 현재 로그인한 사용자 ID 가져오기
  // const currentUserId = useSelector((state: RootState) => state.auth?.user?.id);

  // 히스토리 데이터 가져오기
  const { 
    data: historyData, 
    isLoading, 
    isError 
  } = useUserHistory(user_pk);

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
        const response = await apiClient.get(`/api/tests/${test_type}`);
        
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

  // historyData를 사용하여 컴포넌트 렌더링 업데이트
  useEffect(() => {
    if (historyData) {
      console.log('히스토리 데이터 로드됨:', historyData);
    }
  }, [historyData]);


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
          {isLoading ? (
            <div>로딩 중...</div>
          ) : isError ? (
            <div>데이터를 불러오는 중 오류가 발생했습니다.</div>
          ) : historyData ? (
            <AverageGradeChart averageScore={historyData.average_score} />
          ) : (
            <div>데이터가 없습니다.</div>
          )}
        </section>

        <section className={styles.section}>
          <h2>모의고사 기록</h2>
          {isLoading ? (
            <div>로딩 중...</div>
          ) : isError ? (
            <div>데이터를 불러오는 중 오류가 발생했습니다.</div>
          ) : historyData?.test_history && historyData.test_history.length > 0 ? (
            <div className={styles.records}>
              {historyData.test_history.map((record) => {
                const testDate = new Date(record.test_date);
                const formattedDate = `${testDate.getFullYear()}년 ${testDate.getMonth() + 1}월 ${testDate.getDate()}일`;
                
                // 점수 정보가 없을 경우 기본값 설정
                const grade = record.test_score || '평가 대기중';
                
                return (
                  <RecordItem 
                    key={record.id}
                    date={formattedDate}
                    grade={grade}
                    scores={{
                      description: "결과 대기중",
                      roleplay: "결과 대기중",
                      impromptu: "결과 대기중"
                    }}
                  />
                );
              })}
            </div>
          ) : (
            <div>모의고사 기록이 없습니다.</div>
          )}
        </section>
      </main>
    </div>
  );
}

export default TestMain;