import styles from "./TestMain.module.css";
import TestTypeButton from "@/components/test/TestTypeButton";
import AverageGradeChart from "@/components/test/AverageGradeChart";
import RecordItem from "@/components/test/RecordItem";
import apiClient from "@/api/apiClient";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { testActions } from "@/store/testSlice";
import { useEffect, useState } from "react";
import { useUserHistory } from "@/hooks/useHistory";
import Navbar from "@/components/common/Navbar";

function TestMain() {
  // 히스토리 데이터 가져오기
  const { data: historyData, isLoading } = useUserHistory();

  // 비동기 액션 연결
  const dispatch = useDispatch();

  // 테스트 배포 : 문제 생성 모의고사 3회, 랜덤 단일문제 5회
  // 모의고사 횟수, 단일 랜덤문제 횟수
  const testCounts = historyData?.test_counts?.test_count;
  const randomCounts = historyData?.test_counts?.random_problem;

  const testRemaining = testCounts?.remaining;
  const testLimit = testCounts?.limit;

  const randomRemaining = randomCounts?.remaining;
  const randomLimit = randomCounts?.limit;

  console.log("testRemaining", testRemaining);
  console.log("randomRemaining", randomRemaining);

  // 시험 생성 로딩
  const [loadingTestType, setLoadingTestType] = useState<number | null>(null);

  const navigate = useNavigate();

  // 생성 버튼 핸들링-axios 요청
  const handleCreateTest = async (test_type: number) => {
    // test_type에 따라 조건 확인
    let canProceed = false;

    if (test_type === 2 && randomRemaining && randomRemaining > 0) {
      // 랜덤 단일 문제인 경우, 남은 횟수가 있는지 확인
      canProceed = true;
    } else if (
      (test_type === 0 || test_type === 1) &&
      testRemaining &&
      testRemaining > 0
    ) {
      // 속성 또는 실전 모의고사인 경우, 남은 횟수가 있는지 확인
      canProceed = true;
    }

    if (canProceed) {
      try {
        // 로딩 상태 시작
        setLoadingTestType(test_type);
        const response = await apiClient.post(`/tests/${test_type}`);

        // 응답 데이터를 Redux에 저장
        dispatch(testActions.setCurrentTest(response.data));

        console.log("테스트 데이터가 Redux에 저장됨:", response.data);

        // 페이지 이동
        navigate("/tests/practice");
      } catch (error) {
        console.error("테스트 생성 오류:", error);
        // 에러 처리 로직
      } finally {
        // 로딩 상태 종료
        setLoadingTestType(null);
      }
    } else {
      // 사용 가능한 횟수가 없을 때 사용자에게 알림
      alert(
        `오늘의 ${
          test_type === 2 ? "맛보기" : "모의고사"
        } 응시 최대치를 다 해내셨군요! 너무 멋져요🤗`
      );
    }
  };

  // historyData를 사용하여 컴포넌트 렌더링 업데이트
  useEffect(() => {
    if (historyData) {
      console.log("히스토리 데이터 로드됨:", historyData);
    }
  }, [historyData, isLoading]);

  console.log(historyData)

  return (
    <div className={styles.container}>
      {/* 테스트 배포 : 3회 응시 횟수 제한 추가 필요 */}
      <main className={styles.main}>
        <section className={styles.section1}>
          <h2>시험유형 선택</h2>
          <div className={styles.testTypes}>
            <span className={styles.countLimit}>
              오늘의 응시권 {randomRemaining}/{randomLimit}회🐧
            </span>
            <TestTypeButton
              onClick={() => handleCreateTest(2)}
              title="한 문제 맛보기"
              description="빠르게 현재 레벨 파악하기"
              isLoading={loadingTestType === 2}
            />
            <span className={styles.countLimit}>
              오늘의 응시권 {testRemaining}/{testLimit}회🐟
            </span>

            <TestTypeButton
              onClick={() => handleCreateTest(0)}
              title="속성 모의고사"
              description="바쁜 사람들을 위한 스몰 테스트"
              isLoading={loadingTestType === 0}
            />
            <TestTypeButton
              onClick={() => handleCreateTest(1)}
              title="실전 모의고사"
              description="실제 시험처럼 연습하기"
              isLoading={loadingTestType === 1}
            />
          </div>
        </section>

        <section className={styles.section}>
          <h2>유형별 나의 평균 등급</h2>
          {isLoading ? (
            <div>로딩 중...</div>
          ) : (
            <AverageGradeChart averageScore={historyData?.average_score} />
          )}
        </section>

        <section className={styles.section}>
          <h2>모의고사 기록</h2>
          {isLoading ? (
            <div>로딩 중...</div>
          ) : historyData && historyData.test_history?.length > 0 ? (
            // TestMain.tsx의 변경된 부분
            <div className={styles.records}>
              {historyData.test_history.map((record) => {
                const testDate = new Date(record.test_date);
                const formattedDate = `${testDate.getFullYear()}년 ${
                  testDate.getMonth() + 1
                }월 ${testDate.getDate()}일`;

                return (
                  <RecordItem
                    key={record.id}
                    date={formattedDate}
                    test_pk={record.id}
                  />
                );
              })}
            </div>
          ) : (
            !historyData && (
              <div className={styles.noData}>
                내 기록을 한눈에 볼 수 있어요!
              </div>
            )
          )}
        </section>
      </main>

      <Navbar />
    </div>
  );
}

export default TestMain;
