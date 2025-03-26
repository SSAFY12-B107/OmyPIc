import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import apiClient from "../api/apiClient";

// 문제 정보 인터페이스 정의
export interface Problem {
  _id: string;
  topic_category: string;
  problem_category: string;
  content: string;
}

// 문제 상세 정보 인터페이스 정의
export interface ProblemDetail {
  problem: {
    _id: string;
    content: string;
  };
  user_scripts: any[]; // 필요에 따라 더 구체적인 타입 정의 가능
  test_notes: any[];   // 필요에 따라 더 구체적인 타입 정의 가능
  script_limit: {
    used: number;
    limit: number;
    remaining: number;
  }
}

// 문제 목록 조회를 위한 파라미터 인터페이스
export interface ProblemQueryParams {
  skip: number;
  limit: number;
}

// 문제 목록 조회 API 훅
export const useGetProblems = (category: string) => {
  return useInfiniteQuery<Problem[]>({
    queryKey: ["problems", category],
    queryFn: async ({ pageParam = 0 }) => {
      const response = await apiClient.get<Problem[]>(`/problems/${category}`, {
        params: {
          skip: pageParam,
          limit: 10,
        },
      });
      return response.data;
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      // 마지막 페이지가 비어있거나 요청한 limit보다 적은 수의 결과가 돌아왔다면
      // 더 이상 가져올 데이터가 없는 것으로 판단
      return lastPage.length === 10 ? allPages.length * 10 : undefined;
    },
  });
};

// 문제 상세 조회 API 훅
export const useGetProblemDetail = (problem_id: string) => {
  return useQuery<ProblemDetail>({
    queryKey: ["problem", problem_id],
    queryFn: async () => {
      const response = await apiClient.get<ProblemDetail>(`/problems/detail/${problem_id}`);
      return response.data;
    }
  })
}