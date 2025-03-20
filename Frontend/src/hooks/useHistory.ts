// hooks/useHistory.ts
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/apiClient';

// 타입 정의
export interface TestHistory {
  id: string;
  test_date: string;
  test_type: boolean;
  test_score: string | null;
}

export interface AverageScore {
  total_score: string;
  comboset_score: string;
  roleplaying_score: string;
  unexpected_score: string;
}

export interface UserHistoryResponse {
  average_score: AverageScore;
  test_history: TestHistory[];
}


// 사용자 히스토리 조회 함수
const fetchUserHistory = async (user_pk: number): Promise<UserHistoryResponse> => {
    try {
      const { data } = await apiClient.get(`/api/tests/history/${user_pk}`);
      return data;
    } catch (error) {
      console.error('히스토리 조회 에러:', error);
      throw error;
    }
  };
  
  // 사용자 히스토리 조회 훅
  export const useUserHistory = (user_pk: string | undefined) => {
      // 문자열을 숫자로 변환
  const numericUserId = user_pk ? parseInt(user_pk, 10) : undefined;

    return useQuery({
      queryKey: ['userHistory', user_pk],
      queryFn: () => fetchUserHistory(numericUserId!),
      // userId가 없을 경우 쿼리 실행 중지
      enabled: !!user_pk,

    });
  };