// src/api/homeApi.ts
import { useQuery } from "@tanstack/react-query";
import apiClient from "./apiClient";

// 사용자 정보 인터페이스 정의
export interface User {
  id: string;                 // 고유 식별자
  username: string;           // 1. 사용자 이름
  desiredGrade: string;       // 2. 희망 등급
  currentGrade: string;       // 3. 현재 등급
  daysUntilExam: number;      // 4. 시험까지 남은 기간 (일 수)
  expectedGradeStats: {       // 5. 예상 등급 통계
  date: Date;                 // 예측 날짜
  grade: string;              // 해당 날짜의 예상 등급
  };
  createdAt: Date;            // 사용자 생성 날짜
}

// 회원 정보 전체 조회 API 훅
export const useGetUserInfo = () => {
  return useQuery<User>({
    queryKey: ["userInfo"],
    queryFn: async () => {
      const response = await apiClient.get<User>("/users");
      return response.data;
    },
  });
};