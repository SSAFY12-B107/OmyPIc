// src/api/homeApi.ts
import { useQuery } from "@tanstack/react-query";
import apiClient from "../api/apiClient";

// 사용자 정보 인터페이스 정의
interface UserInfo {
  _id: string;
  name: string;
  email: string;
  current_opic_score: string;
  target_opic_score: string;
  target_exam_date: string;
  is_onboarded: boolean;
  background_survey: Record<string, any>;
  test: {
    test_date: (string | null)[]; // 길이 제한 없는 배열
    test_score: (string | null)[];
  };
}

// 회원 정보 전체 조회 API 훅
export const useGetUserInfo = () => {
  return useQuery<UserInfo>({
    queryKey: ["userInfo"],
    queryFn: async () => {
      const response = await apiClient.get<UserInfo>("/users/");
      return response.data;
    },
  });
};
