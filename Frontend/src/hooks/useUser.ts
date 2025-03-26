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
const API_BASE_URL = 'https://omypic.store/api';

// 에러 응답 타입 정의
interface ErrorResponse {
  detail?: string;
  [key: string]: any;
}

export const useUser = () => {
  const dispatch = useDispatch();
  const { user, isAuthenticated, profileData } = useSelector((state: RootState) => state.auth);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 로그인 상태 확인
  const checkAuth = async () => {
    try {
      dispatch(setLoading(true));

      // 액세스 토큰 가져오기
      const accessToken = sessionStorage.getItem('access_token');
      
      if (!accessToken) {
        dispatch(clearUser());
        return false;
      }

      const response = await fetch(`${API_BASE_URL}/users/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        }
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
    // 세션 스토리지 토큰 제거
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('isOnboarded');
    dispatch(clearUser());
  };

  // 프로필 데이터 업데이트 (로컬 상태 관리)
  const updateProfile = (data: ProfileData) => {
    dispatch(setProfileData(data));
  };

  // 프로필 필드 업데이트 (로컬 상태 관리)
  const updateProfileField = (field: keyof ProfileData, value: string) => {
    dispatch(setProfileField({ field, value }));
  };

  // 프로필 데이터만 서버에 저장 (PUT 메서드 사용)
  const saveProfile = async () => {
    try {
      setIsSubmitting(true);
      dispatch(setLoading(true));

      if (!user) {
        throw new Error('로그인이 필요합니다.');
      }

      // 액세스 토큰 가져오기
      const accessToken = sessionStorage.getItem('access_token');
      
      if (!accessToken) {
        throw new Error('인증 토큰이 없습니다. 다시 로그인해주세요.');
      }

      // API 문서에 맞게 요청 데이터 구성
      const requestData = {
        current_opic_score: profileData.currentGrade || "",
        target_opic_score: profileData.wishGrade || "",
        target_exam_date: profileData.examDate || "",
        is_onboarded: false // 설문 전이므로 onboarded = false
      };

      console.log('프로필 업데이트 요청 데이터:', requestData);

      const response = await fetch(`${API_BASE_URL}/users/`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        const errorData = await response.json() as ErrorResponse;
        console.error('API 오류 응답:', errorData);
        throw new Error(errorData.detail || '프로필 저장에 실패했습니다');
      }

      const result = await response.json();
      dispatch(setUser(result));

      return { success: true, data: result };
    } catch (error) {
      console.error('프로필 저장 오류:', error);
      if (error instanceof Error) {
        dispatch(setError(error.message));
      } else {
        dispatch(setError('알 수 없는 오류가 발생했습니다'));
      }
      return { success: false, error: (error instanceof Error) ? error.message : '알 수 없는 오류가 발생했습니다' };
    } finally {
      setIsSubmitting(false);
      dispatch(setLoading(false));
    }
  };

  // 🔹 사용자가 처음 가입한 경우 - 프로필 생성 (POST)
  const createUserProfile = async (profileWithSurvey: any) => {
    try {
      setIsSubmitting(true);
      dispatch(setLoading(true));
  
      if (!user) {
        throw new Error("로그인이 필요합니다.");
      }

      // 액세스 토큰 가져오기
      const accessToken = sessionStorage.getItem('access_token');
      
      if (!accessToken) {
        throw new Error('인증 토큰이 없습니다. 다시 로그인해주세요.');
      }
      
      console.log("📌 새 사용자 프로필 생성 요청:", JSON.stringify(profileWithSurvey, null, 2));
  
      const response = await fetch(`${API_BASE_URL}/users/`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${accessToken}`
        },
        body: JSON.stringify(profileWithSurvey),
      });
  
      const result = await response.json() as ErrorResponse;
  
      if (!response.ok) {
        console.error("❌ 서버 응답 오류:", JSON.stringify(result, null, 2));
        sessionStorage.clear();
        throw new Error(result.detail || "사용자 프로필 생성에 실패했습니다.");
      }
  
      console.log("✅ 사용자 생성 성공:", result);
      dispatch(setUser(result));
      
      // 온보딩 완료 상태 저장
      sessionStorage.setItem('isOnboarded', 'true');
      
      return { success: true, data: result };
    } catch (error) {
      console.error("❌ 사용자 생성 오류:", error);
      return { success: false, error: error instanceof Error ? error.message : "알 수 없는 오류 발생" };
    } finally {
      setIsSubmitting(false);
      dispatch(setLoading(false));
    }
  };

  // 🔹 설문 데이터까지 포함하여 사용자 정보 업데이트 (PUT)
  const saveProfileAndSurvey = async (surveyData: any) => {
    try {
      setIsSubmitting(true);
      dispatch(setLoading(true));
  
      if (!user) {
        throw new Error("로그인이 필요합니다.");
      }

      // 액세스 토큰 가져오기
      const accessToken = sessionStorage.getItem('access_token');
      
      if (!accessToken) {
        throw new Error('인증 토큰이 없습니다. 다시 로그인해주세요.');
      }
  
      // API 문서에 맞게 요청 데이터 구성
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
  
      console.log("📌 사용자 정보 업데이트 요청:", JSON.stringify(requestData, null, 2));
  
      const response = await fetch(`${API_BASE_URL}/users/`, {
        method: "PUT",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${accessToken}`
        },
        body: JSON.stringify(requestData),
      });
  
      const result = await response.json() as ErrorResponse;
  
      if (!response.ok) {
        console.error("❌ 서버 응답 오류:", JSON.stringify(result, null, 2));
        sessionStorage.clear();
        throw new Error(result.detail || "설문 저장에 실패했습니다.");
      }
  
      console.log("✅ 설문 저장 성공:", result);
      dispatch(setUser(result));
      
      // 온보딩 완료 상태 저장
      sessionStorage.setItem('isOnboarded', 'true');
      
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
    createUserProfile, // 새 사용자 생성 함수 추가
    saveProfileAndSurvey,
  };
};