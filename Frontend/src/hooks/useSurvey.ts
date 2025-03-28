import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { setUser, setError } from '../store/authSlice';
import apiClient from '../api/apiClient';


// 서베이 데이터 인터페이스
export interface SurveyData {
  profession: string | number;
  is_student: boolean;
  studied_lecture: string | number;
  living_place: string | number;
  info: (string | number)[];
}

export const useSurvey = () => {
  const dispatch = useDispatch();
  const queryClient = useQueryClient();
  
  // Redux에서 필요한 상태 가져오기
  const { profileData } = useSelector((state: RootState) => state.auth);

  // 설문 데이터와 함께 프로필 업데이트 뮤테이션 (PUT 요청만 사용)
  const profileWithSurveyMutation = useMutation({
    mutationFn: async (surveyData: SurveyData) => {
      // 요청 데이터 구성
      const requestData = {
        current_opic_score: profileData.currentGrade || "",
        target_opic_score: profileData.wishGrade || "",
        target_exam_date: profileData.examDate || "",
        is_onboarded: true, // 설문 완료 후이므로 true
        background_survey: {
          profession: surveyData.profession || 0,
          is_student: surveyData.is_student || false,
          studied_lecture: surveyData.studied_lecture || 0,
          living_place: surveyData.living_place || 0,
          info: surveyData.info || []
        }
      };
      
      // 사용자가 존재하는지 확인
      if (!sessionStorage.getItem('access_token')) {
        throw new Error('로그인이 필요합니다.');
      }

      // PUT 요청으로 업데이트 (새 프로필 생성 또는 기존 프로필 업데이트)
      const response = await apiClient.put('/users/', requestData);
      return response.data;
    },
    onSuccess: (data) => {
      // 성공 시 사용자 정보 업데이트 및 캐시 무효화
      dispatch(setUser(data));
      sessionStorage.setItem('isOnboarded', 'true');
      queryClient.invalidateQueries({ queryKey: ['user'] });
    },
    onError: (error: any) => {
      // 에러 처리
      console.error('설문 저장 오류:', error);
      
      const errorMessage = error.response?.data?.detail || '설문 저장에 실패했습니다.';
      dispatch(setError(errorMessage));
      
      // 인증 에러인 경우 세션 클리어 (apiClient에서 처리할 수도 있음)
      if (error.response?.status === 401) {
        sessionStorage.clear();
      }
    }
  });

  // 설문 데이터 저장 함수
  const saveProfileAndSurvey = async (surveyData: SurveyData) => {
    try {
      const result = await profileWithSurveyMutation.mutateAsync(surveyData);
      return { success: true, data: result };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : '알 수 없는 오류 발생' 
      };
    }
  };

  return {
    saveProfileAndSurvey,
    isSaving: profileWithSurveyMutation.isPending
  };
};