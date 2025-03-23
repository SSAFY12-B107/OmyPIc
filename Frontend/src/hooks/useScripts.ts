import { useQuery, useMutation } from "@tanstack/react-query";
import apiClient from "../api/apiClient";

// 기본 질문 응답 인터페이스 정의
export interface QuestionsResponse {
  content: string, // String -> string으로 수정
  questions: string[];
}

// 꼬리질문 요청 인터페이스 정의
export interface CustomQuestionsRequest {
  question1: string;
  question2: string;
  question3: string;
}

// 스크립트 작성 요청 인터페이스 정의
export interface CreateScriptRequest {
  type: "basic" | "custom";
  basic_answers: {
    answer1: string;
    answer2: string;
    answer3: string;
  };
  custom_answers: {
    answer1: string;
    answer2: string;
    answer3: string;
  };
}

// 스크립트 작성 응답 인터페이스 정의
export interface CreateScriptResponse {
  _id: string;
  content: string;
  created_at: string;
  is_script: boolean;
}

// 기본 질문 목록 조회 API 훅
export const useGetBasicQuestions = (problemId: string) => {
  return useQuery<QuestionsResponse>({
    queryKey: ["basic-questions", problemId],
    queryFn: async () => {
      const response = await apiClient.get<QuestionsResponse>(
        `/problems/${problemId}/basic-question`
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
    { problemId: string; answers: CustomQuestionsRequest } // 문제 ID와 답변 데이터
  >({
    mutationFn: async ({ problemId, answers }) => {
      const response = await apiClient.post<QuestionsResponse>(
        `/problems/${problemId}/custom-question`,
        answers
      );
      return response.data;
    },
  });
};

// 스크립트 작성 API 훅
export const useCreateScript = () => {
  return useMutation<
    CreateScriptResponse,
    Error,
    { problemId: string; scriptData: CreateScriptRequest }
  >({
    mutationFn: async ({ problemId, scriptData }) => {
      const response = await apiClient.post<CreateScriptResponse>(
        `/problems/${problemId}/scripts`,
        scriptData
      );
      return response.data;
    },
  });
};