// src/hooks/useUserInfo.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "../api/apiClient";
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { clearUser } from '../store/authSlice';

interface BackgroundSurvey {
  profession: number;
  is_student: boolean;
  studied_lecture: number;
  living_place: number;
  info: string[];
}

// 사용자 정보 인터페이스 정의
interface UserInfo {
  _id: string;
  name: string;
  email: string;
  current_opic_score: string;
  target_opic_score: string;
  target_exam_date: string;
  is_onboarded: boolean;
  background_survey: BackgroundSurvey;
  test: {
    test_date: (string | null)[];
    test_score: (string | null)[];
  };
}

// 회원 정보 전체 조회 API 훅
export const useGetUserInfo = () => {
  return useQuery<UserInfo>({
    queryKey: ["userInfo"],
    queryFn: async () => {
      const response = await apiClient.get<UserInfo>("/users/me");
      return response.data;
    },
  });
};

// 로그아웃 API 훅
export const useLogout = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  return useMutation({
    mutationFn: async () => {
      return await apiClient.post('/auth/logout');
    },
    onSuccess: () => {
      // 1. 세션 스토리지에서 토큰 제거
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('isOnboarded');
      
      // 2. Redux 스토어에서 사용자 정보 초기화
      dispatch(clearUser());
      
      // 3. TanStack Query 캐시 초기화
      queryClient.clear();
      
      // 4. 로그인 페이지로 리다이렉트
      navigate('/auth/login');
    },
    onError: (error) => {
      console.error('로그아웃 실패:', error);
      
      // 에러가 발생해도 클라이언트 측에서는 로그아웃 처리를 진행
      sessionStorage.removeItem('access_token');
      dispatch(clearUser());
      queryClient.clear();
      navigate('/auth/login');
    }
  });
};