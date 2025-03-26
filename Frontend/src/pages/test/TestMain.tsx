import styles from "./TestMain.module.css";
import TestTypeButton from "@/components/test/TestTypeButton";
import AverageGradeChart from "@/components/test/AverageGradeChart";
import RecordItem from "@/components/test/RecordItem";
import apiClient from "@/api/apiClient";
import { useLocation, useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { testActions } from "@/store/testSlice";
import { useEffect, useState } from "react";
import { useUserHistory } from "@/hooks/useHistory";
import Navbar from "@/components/common/Navbar";

function TestMain() {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();

  // location.state에서 최근 테스트 정보 확인
  const { recentTestId, feedbackReady } = location.state || {};

  console.log("recenttestId", recentTestId);

  // 폴링 활성화 여부 결정 - feedbackReady가 true면 폴링 비활성화
  const shouldPoll = recentTestId && !feedbackReady;
  console.log('shouldpoll',shouldPoll)

  // 이미 확인된 피드백 상태 추적
  const [feedbackChecked, setFeedbackChecked] = useState(
    feedbackReady || false
  );

  // 히스토리 데이터 가져오기 (폴링 기능 통합)
  const { 
    data: historyData, 
    isLoading, 
    startPolling,
    stopPolling,
    feedbackStatus
  } = useUserHistory({
    enablePolling: shouldPoll && !feedbackChecked,
    recentTestId,
    onFeedbackReady: (testHistory) => {
      // 피드백이 준비되면 상태 업데이트
      setFeedbackChecked(true);
      
      // navigate 자기자신 호출 제거 - 이것이 무한 루프의 원인이었습니다
    }
  });

  // 폴링 상태 관리
  useEffect(() => {
    if (shouldPoll && !feedbackChecked) {
      startPolling();
    } else {
      stopPolling();
    }
    
    // 피드백 상태가 변경되면 폴링 중지
    if (feedbackStatus) {
      stopPolling();
      setFeedbackChecked(true);
    }
  }, [shouldPoll, feedbackChecked, startPolling, stopPolling, feedbackStatus]);

  // 테스트 배포 : 문제 생성 모의고사 3회, 랜덤 단일문제 5회
  // 모의고사 횟수, 단일 랜덤문제 횟수
  const testCounts = historyData?.test_counts?.test_count;
  const randomCounts = historyData?.test_counts?.random_problem;

  const testRemaining = testCounts?.remaining;
  const testLimit = testCounts?.limit;

  const randomRemaining = randomCounts?.remaining;
  const randomLimit = randomCounts?.limit;

  // console.log("testRemaining", testRemaining);
  // console.log("randomRemaining", randomRemaining);

  // 시험 생성 로딩
  const [loadingTestType, setLoadingTestType] = useState<number | null>(null);

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

        console.log("테스트 생성완료!");
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

  // { /tests/라는 주소로 왔다면 (
  //   setIsNavigated(true)
  //   historydata 호출 그만
  // )}
  console.log("메인페이지에서 history 호출", historyData);

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
                    record={record}
                  />
                );
              })}
            </div>
          ) : (
            !isLoading && (
              <div className={styles.noData}>
                내 기록을 한눈에 볼 수 있어요 🤗
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
