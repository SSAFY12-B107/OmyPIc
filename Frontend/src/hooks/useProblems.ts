import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import apiClient from "./apiClient";

// 문제 정보 인터페이스 정의
export interface Problem {
  id: string;
  topic_category: string;
  problem_category: string;
  content: string;
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
