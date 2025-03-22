// hooks/useFeedback.ts
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/apiClient';

// 종합 피드백 객체 타입 정의
export interface MultipleFeedback {
    total_feedback: string;
    paragraph: string;
    vocabulary: string;
    spoken_amount: string;
  }

// 개별 문제 피드백 객체 타입 정의
export interface SingleFeedback {
    paragraph: string;
    vocabulary: string;
    spoken_amount: string;

  }

  

// 개별 문제 데이터 타입 정의
export interface ProblemData {
  problem_id: string;
  problem_category: string;
  topic_category: string;
  problem: string;
  user_response: string | null;
  score: string | null;
  feedback: SingleFeedback | null;
}

// 테스트 데이터 타입 정의
export interface TestFeedbackData {
  _id: string; // 문제 pk (ex 모의고사 1회)
  user_id: string;
  test_type: boolean;
  test_date: string;
  test_score: {
    total_score : string | null;
    comboset_score : string | null;
    roleplaying_score : string | null;
    unexpected_score : string | null;
  };
  test_feedback: MultipleFeedback | null;
  problem_data: {
    [key: string]: ProblemData;
  };
}

// 테스트 피드백 조회 함수
const fetchTestFeedback = async (test_pk: string): Promise<TestFeedbackData> => {
  try {
    const { data } = await apiClient.get(`/tests/${test_pk}`);
    return data;
  } catch (error) {
    console.error('피드백 조회 에러:', error);
    throw error;
  }
};

// 테스트 피드백 조회 훅
export const useFeedback = (test_pk: string | undefined) => {

  return useQuery({
    queryKey: ['testFeedback', test_pk],
    queryFn: () => fetchTestFeedback(test_pk!),

    enabled: !!test_pk 
  });
};

// 특정 문제 데이터를 가져오는 유틸리티 함수
export const getProblemData = (
  feedbackData: TestFeedbackData | undefined,
  problemNumber: number
): ProblemData | undefined => {
  if (!feedbackData || !feedbackData.problem_data) return undefined;
  return feedbackData.problem_data[problemNumber.toString()];
};

// 테스트의 총 문제 수를 계산하는 유틸리티 함수
export const getTotalProblems = (feedbackData: TestFeedbackData | undefined): number => {
  if (!feedbackData || !feedbackData.problem_data) return 0;
  return Object.keys(feedbackData.problem_data).length;
};