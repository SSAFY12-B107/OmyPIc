import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  setUser, 
  clearUser, 
  setProfileData,
  setProfileField,
  setLoading,
  setError,
  ProfileData
} from '../store/authSlice';
import { RootState } from '../store/store';

// API 기본 URL
const API_BASE_URL = 'http://localhost:8000/api';

export const useUser = () => {
  const dispatch = useDispatch();
  const { user, isAuthenticated, profileData } = useSelector((state: RootState) => state.auth);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 로그인 상태 확인
  const checkAuth = async () => {
    try {
      dispatch(setLoading(true));

      const response = await fetch(`${API_BASE_URL}/users/`, {
        credentials: 'include', // 쿠키 기반 인증을 사용할 경우
      });

      if (response.ok) {
        const userData = await response.json();
        dispatch(setUser(userData));
        return true;
      } else {
        dispatch(clearUser());
        return false;
      }
    } catch (error) {
      console.error('인증 확인 실패:', error);
      dispatch(clearUser());
      return false;
    } finally {
      dispatch(setLoading(false));
    }
  };

  // 로그아웃
  const logout = () => {
    dispatch(clearUser());
  };

  // 프로필 데이터 업데이트
  const updateProfile = (data: ProfileData) => {
    dispatch(setProfileData(data));
  };

  // 프로필 필드 업데이트
  const updateProfileField = (field: keyof ProfileData, value: string) => {
    dispatch(setProfileField({ field, value }));
  };

  // 프로필 데이터 서버에 저장
  const saveProfile = async () => {
    try {
      setIsSubmitting(true);
      dispatch(setLoading(true));

      if (!user) {
        throw new Error('로그인이 필요합니다.');
      }

      const requestData = {
        name: user.name,
        auth_provider: user.auth_provider,
        email: user.email,
        current_opic_score: profileData.currentGrade,
        target_opic_score: profileData.wishGrade,
        target_exam_date: profileData.examDate
      };

      console.log('requestData', requestData)

      const response = await fetch(`api/users`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        throw new Error('프로필 저장에 실패했습니다');
      }

      const result = await response.json();
      dispatch(setUser(result));

      return { success: true, data: result };
    } catch (error) {
      console.error('프로필 저장 오류:', error);
      if (error instanceof Error) {
        dispatch(setError(error.message));
      } else {
        dispatch(setError('An unknown error occurred'));
      }
      return { success: false, error: (error instanceof Error) ? error.message : 'An unknown error occurred' };
    } finally {
      setIsSubmitting(false);
      dispatch(setLoading(false));
    }
  };

  // 🔹 설문 데이터 저장 요청
  const saveProfileAndSurvey = async (surveyData: any) => {
    try {
      setIsSubmitting(true);
      dispatch(setLoading(true));
  
      if (!user) {
        throw new Error("로그인이 필요합니다.");
      }
  
      // 프로필 및 설문 데이터를 모두 포함한 requestData 구성
      const requestData = {
        name: user.name,  // ✅ 프로필 정보 추가
        email: user.email,
        auth_provider: user.auth_provider,
        provider_id: user.provider_id || "",
        profile_image: user.profile_image || "",
        current_opic_score: profileData.wishGrade || "",
        target_opic_score: profileData.wishGrade || "",
        target_exam_date: profileData.examDate || null,
        is_onboarded: true,
        background_survey: {
          profession: surveyData.profession,
          is_student: surveyData.is_student,
          studied_lecture: surveyData.studied_lecture,
          living_place: surveyData.living_place,
          info: surveyData.info || []
        }
      };
  
      console.log("📌 서버로 보내는 데이터:", JSON.stringify(requestData, null, 2));
  
      const response = await fetch(`${API_BASE_URL}/users/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData),
      });
  
      const result = await response.json();
  
      if (!response.ok) {
        console.error("❌ 서버 응답 오류:", JSON.stringify(result, null, 2));
        throw new Error(result.detail || "설문 저장에 실패했습니다.");
      }
  
      console.log("✅ 서버 응답 성공:", result);
      return { success: true, data: result };
    } catch (error) {
      console.error("❌ 설문 저장 오류:", error);
      return { success: false, error: error instanceof Error ? error.message : "알 수 없는 오류 발생" };
    } finally {
      setIsSubmitting(false);
      dispatch(setLoading(false));
    }
  };
  
  
  
  return {
    user,
    isAuthenticated,
    profileData,
    isSubmitting,
    checkAuth,
    logout,
    updateProfile,
    updateProfileField,
    saveProfile,
    saveProfileAndSurvey, // 추가된 함수
  };
};
