// hooks/useHistory.ts
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/apiClient';
import { useCallback, useState, useEffect } from 'react';

export interface Scores {
  total_score: string | null;
  comboset_score: string | null;
  roleplaying_score: string | null;
  unexpected_score: string | null;
}

export interface TestHistory {
  id: string;
  overall_feedback_status: string;
  test_date: string;
  test_type: boolean;
  test_score: Scores | null;
}

export interface AverageScore {
  total_score: string | null;
  comboset_score: string | null;
  roleplaying_score: string | null;
  unexpected_score: string | null;
}

export interface UserHistoryResponse {
  average_score: AverageScore;
  test_history: TestHistory[];
  test_counts: {
    test_count: {
      used: number;
      limit: number;
      remaining: number;
    },
    random_problem: {
      used: number;
      limit: number;
      remaining: number;
    }
  }
}
// 사용자 히스토리 조회 함수
const fetchUserHistory = async (): Promise<UserHistoryResponse> => {
  try {
    const { data } = await apiClient.get('/tests/history');
    console.log('히스토리 데이터 조회')
    return data;
  } catch (error) {
    console.error('히스토리 조회 에러:', error);
    throw error;
  }
};

// 폴링이 적용된 사용자 히스토리 조회 훅
export const useUserHistory = (options?: {
  enablePolling?: boolean; // 폴링 활성화 여부
  pollingInterval?: number;
  recentTestId?: string; // 최근 테스트 id 값 
  onFeedbackReady?: (testHistory: TestHistory) => void; // 콜백함수 
}) => {
  const {
    enablePolling = false,
    pollingInterval = 10000, // 1초 
    recentTestId,
    onFeedbackReady
  } = options || {};

  // 폴링 상태 추적 
  const [isPolling, setIsPolling] = useState(enablePolling);

   // 피드백 준비 상태
  const [feedbackStatus, setFeedbackStatus] = useState<boolean>(false);

  // 폴링 시작/중지 함수
  const startPolling = useCallback(() => setIsPolling(true), []);
  const stopPolling = useCallback(() => setIsPolling(false), []);

  // 기본 쿼리 설정
  const queryResult = useQuery({
    queryKey: ['userHistory'],
    queryFn: fetchUserHistory,
    refetchInterval: isPolling ? pollingInterval : false,
    staleTime: isPolling ? 0 : 60 * 60 * 1000, // 1시간 동안 캐시 데이터 사용// 3초 후 다시 받아오겠다  
  });

  // 데이터 변경 감지
  const { data } = queryResult;
  
  useEffect(() => {
    if (data && recentTestId && onFeedbackReady) {
      const testHistory = data.test_history.find(test => test.id === recentTestId);
      
      if (testHistory && 
          testHistory.overall_feedback_status === 'completed' && 
          testHistory.test_score !== null) {
        
        // 피드백이 준비되면 콜백 실행 및 폴링 중지
        setFeedbackStatus(true); // 피드백 상태 업데이트
        stopPolling();
        onFeedbackReady(testHistory);
      }
    }
  }, [data, recentTestId, onFeedbackReady, stopPolling, feedbackStatus]);

  // enablePolling 값이 변경될 때 폴링 상태 업데이트
  useEffect(() => {
    setIsPolling(enablePolling);
  }, [enablePolling]);

  // 컴포넌트 언마운트 시 폴링 중지
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  // 쿼리 결과와 폴링 제어 함수를 함께 반환
  return {
    ...queryResult,
    isPolling,
    startPolling,
    stopPolling,
    feedbackStatus

  };
};