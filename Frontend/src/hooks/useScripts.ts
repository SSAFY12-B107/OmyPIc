import { useQuery, useMutation } from "@tanstack/react-query";
import apiClient from "../api/apiClient";

// 기본 질문 응답 인터페이스 정의
export interface QuestionsResponse {
  questions: string[];
}

// 요청 본문 인터페이스 정의
export interface CreateScriptRequest {
  answers: string[]; // 사용자가 입력한 질문에 대한 답변 배열
}

// 응답 인터페이스 정의
export interface CreateScriptResponse {
  script: string; // 생성된 스크립트 내용
}

// 기본 질문 목록 조회 API 훅
export const useGetBasicQuestions = (problemId: string) => {
  return useQuery<QuestionsResponse>({
    queryKey: ["basic-questions", problemId],
    queryFn: async () => {
      const response = await apiClient.get<QuestionsResponse>(
        `/problems/${problemId}/basic-questions`
      );
      return response.data;
    },
  });
};

// AI 꼬리질문 생성 API 훅
export const useGenerateCustomQuestions = () => {
  return useMutation<
    QuestionsResponse, // 응답 데이터 타입
    Error, // 에러 타입
    string // 입력 변수 타입 (문제 ID만)
  >({
    mutationFn: async (problemId) => {
      const response = await apiClient.post<QuestionsResponse>(
        `/problems/${problemId}/custom-questions`
      );
      return response.data;
    },
  });
};

// 스크립트 작성 API 훅
export const useCreateScript = () => {
  return useMutation<
    CreateScriptResponse, // 응답 데이터 타입
    Error, // 에러 타입
    { problemId: string; answers: string[] } // 입력 변수 타입
  >({
    mutationFn: async ({ problemId, answers }) => {
      const response = await apiClient.post<CreateScriptResponse>(
        `/problems/${problemId}/scripts`,
        { answers }
      );
      return response.data;
    },
  });
};
