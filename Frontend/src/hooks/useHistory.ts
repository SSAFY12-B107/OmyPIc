// hooks/useHistory.ts
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/apiClient';


export interface Scores {
  total_score : string | null ;
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
  average_score: AverageScore ;
  test_history: TestHistory[];
  test_counts : {
    test_count: {
      used: number;
      limit: number;
      remaining:number;
    },
    random_problem :{
      used:number;
      limit:number;
      remaining:number;
    }
  }
}



// 사용자 히스토리 조회 함수
const fetchUserHistory = async (user_pk: string): Promise<UserHistoryResponse> => {
    try {
      const { data } = await apiClient.get(`/tests/history/${user_pk}`);
      return data;

  
    } catch (error) {

      console.error('히스토리 조회 에러:', error);
      
      throw error;
    }
  };
  
  // 사용자 히스토리 조회 훅
  export const useUserHistory = (user_pk: string | undefined) => {

    return useQuery({
      queryKey: ['userHistory', user_pk],
      queryFn: () => fetchUserHistory(user_pk!),
      // userId가 없을 경우 쿼리 실행 중지
      enabled: !!user_pk,

    });
  };