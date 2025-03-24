// src/hooks/useUser.ts
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
import { RootState } from '../store';

// API 기본 URL
const API_BASE_URL = 'http://localhost:8000/api';

export const useUser = () => {
  const dispatch = useDispatch();
  const { user, isAuthenticated, profileData } = useSelector((state: RootState) => state.auth);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 로그인 상태 확인
  const checkAuth = async () => {
    try {
      const accessToken = sessionStorage.getItem('access_token');
      if (!accessToken) return false;
      
      dispatch(setLoading(true));
      
      const response = await fetch(`${API_BASE_URL}/users/me`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      
      if (response.ok) {
        const userData = await response.json();
        dispatch(setUser(userData));
        return true;
      } else {
        dispatch(clearUser());
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('refresh_token');
        sessionStorage.removeItem('isOnboarded');
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
    // Redux 상태 초기화
    dispatch(clearUser());
    
    // 세션 스토리지 초기화
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    sessionStorage.removeItem('isOnboarded');
    sessionStorage.removeItem('user');
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
      
      const accessToken = sessionStorage.getItem('access_token');
      if (!accessToken) {
        throw new Error('인증되지 않았습니다');
      }

      const response = await fetch(`${API_BASE_URL}/users/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          current_opic_score: profileData.currentGrade,
          target_opic_score: profileData.wishGrade,
          target_exam_date: profileData.examDate
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || '프로필 저장에 실패했습니다');
      }

      const result = await response.json();
      
      // 사용자 정보 업데이트
      dispatch(setUser({
        ...user,
        current_opic_score: profileData.currentGrade,
        target_opic_score: profileData.wishGrade,
        target_exam_date: profileData.examDate
      }));

      return { success: true, data: result };
    } catch (error) {
      console.error('프로필 저장 오류:', error);
      const errorMsg = error instanceof Error ? error.message : '프로필 저장 중 오류가 발생했습니다';
      dispatch(setError(errorMsg));
      return { success: false, error: errorMsg };
    } finally {
      setIsSubmitting(false);
      dispatch(setLoading(false));
    }
  };

  // 서베이 데이터 서버에 저장
  const submitSurvey = async (surveyData: any) => {
    try {
      setIsSubmitting(true);
      dispatch(setLoading(true));
      
      const accessToken = sessionStorage.getItem('access_token');
      if (!accessToken) {
        throw new Error('인증되지 않았습니다');
      }

      const response = await fetch(`${API_BASE_URL}/users/survey`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(surveyData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || '서베이 제출에 실패했습니다');
      }

      const result = await response.json();
      
      // 사용자 정보 업데이트 (onboarded 상태 포함)
      dispatch(setUser({
        ...user,
        is_onboarded: true,
        background_survey: surveyData
      }));
      
      // 온보딩 완료 상태 저장
      sessionStorage.setItem('isOnboarded', 'true');

      return { success: true, data: result };
    } catch (error) {
      console.error('서베이 제출 오류:', error);
      const errorMsg = error instanceof Error ? error.message : '서베이 제출 중 오류가 발생했습니다';
      dispatch(setError(errorMsg));
      return { success: false, error: errorMsg };
    } finally {
      setIsSubmitting(false);
      dispatch(setLoading(false));
    }
  };

    // 프로필과 서베이 데이터를 함께 저장하는 함수
    const saveProfileAndSurvey = async (surveyData: any) => {
    try {
      setIsSubmitting(true);
      dispatch(setLoading(true));
      
      const accessToken = sessionStorage.getItem('access_token');
      if (!accessToken) {
        throw new Error('인증되지 않았습니다');
      }
  
      // 현재 사용자 정보 가져오기
      const userStr = sessionStorage.getItem('user');
      if (!userStr) {
        throw new Error('사용자 정보를 찾을 수 없습니다');
      }
      
      const user = JSON.parse(userStr);
      
      // POST /api/users/에 맞는 요청 데이터 구성
      const requestData = {
        name: user.name,
        auth_provider: user.auth_provider,
        email: user.email || "user@example.com", // 필요시 기본값 제공
        current_opic_score: profileData.currentGrade,
        target_opic_score: profileData.wishGrade,
        target_exam_date: profileData.examDate,
        background_survey: surveyData
      };
      
      console.log('저장할 통합 데이터:', requestData);
      
      // 사용자 생성 API 호출
      const response = await fetch(`${API_BASE_URL}/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(requestData)
      });
      
      // 응답 처리
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API 오류 응답:', errorText);
        try {
          const errorData = JSON.parse(errorText);
          throw new Error(errorData.detail || '데이터 저장에 실패했습니다');
        } catch (e) {
          throw new Error('데이터 저장에 실패했습니다: ' + errorText);
        }
      }
      
      const result = await response.json();
      
      // 사용자 정보 업데이트
      dispatch(setUser({
        ...user,
        current_opic_score: profileData.currentGrade,
        target_opic_score: profileData.wishGrade,
        target_exam_date: profileData.examDate,
        is_onboarded: true,
        background_survey: surveyData
      }));
      
      // 세션 스토리지 업데이트
      sessionStorage.setItem('user', JSON.stringify(result));
      sessionStorage.setItem('isOnboarded', 'true');
      
      return { success: true, data: result };
    } catch (error) {
      console.error('데이터 저장 오류:', error);
      const errorMsg = error instanceof Error ? error.message : '데이터 저장 중 오류가 발생했습니다';
      dispatch(setError(errorMsg));
      return { success: false, error: errorMsg };
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
    submitSurvey,
    saveProfileAndSurvey
  };
};