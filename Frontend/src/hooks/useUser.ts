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

      // 현재 유저 정보 가져오기
      let userData = user;
      if (!userData) {
        const userStr = sessionStorage.getItem('user');
        if (userStr) {
          userData = JSON.parse(userStr);
        } else {
          userData = {
            name: '사용자',
            auth_provider: 'google',
            email: 'user@example.com'
          };
        }
      }

      // 프로필 요청 데이터 구성
      const requestData = {
        name: userData.name || '사용자',
        auth_provider: userData.auth_provider || 'google',
        email: userData.email || 'user@example.com',
        current_opic_score: profileData.currentGrade,
        target_opic_score: profileData.wishGrade,
        target_exam_date: profileData.examDate
      };

      // users 엔드포인트에 POST 요청
      const response = await fetch(`${API_BASE_URL}/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || '프로필 저장에 실패했습니다');
      }

      const result = await response.json();
      
      // 사용자 정보 업데이트
      dispatch(setUser({
        ...result,
        current_opic_score: profileData.currentGrade,
        target_opic_score: profileData.wishGrade,
        target_exam_date: profileData.examDate
      }));

      // 세션 스토리지에 사용자 정보 저장
      try {
        sessionStorage.setItem('user', JSON.stringify(result));
      } catch (e) {
        console.warn('사용자 정보 저장 실패:', e);
      }

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

      // 현재 유저 정보 가져오기
      let userData = user;
      if (!userData) {
        const userStr = sessionStorage.getItem('user');
        if (userStr) {
          userData = JSON.parse(userStr);
        } else {
          userData = {
            name: '사용자',
            auth_provider: 'google',
            email: 'user@example.com'
          };
        }
      }

      // 요청 데이터 구성
      const requestData = {
        name: userData.name || '사용자',
        auth_provider: userData.auth_provider || 'google',
        email: userData.email || 'user@example.com',
        current_opic_score: userData.current_opic_score || profileData.currentGrade,
        target_opic_score: userData.target_opic_score || profileData.wishGrade,
        target_exam_date: userData.target_exam_date || profileData.examDate,
        background_survey: surveyData
      };

      // users 엔드포인트에 POST 요청
      const response = await fetch(`${API_BASE_URL}/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || '서베이 제출에 실패했습니다');
      }

      const result = await response.json();
      
      // 사용자 정보 업데이트 (onboarded 상태 포함)
      dispatch(setUser({
        ...result,
        is_onboarded: true,
        background_survey: surveyData
      }));
      
      // 온보딩 완료 상태 저장
      sessionStorage.setItem('isOnboarded', 'true');
      
      // 세션 스토리지에 사용자 정보 저장
      try {
        sessionStorage.setItem('user', JSON.stringify(result));
      } catch (e) {
        console.warn('사용자 정보 저장 실패:', e);
      }

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
  
      // 현재 사용자 정보 확인
      let userData = user;
      
      // Redux에 사용자 정보가 없는 경우 세션 스토리지 확인
      if (!userData) {
        const userStr = sessionStorage.getItem('user');
        if (userStr) {
          userData = JSON.parse(userStr);
        } else {
          userData = {
            name: '사용자',
            auth_provider: 'google',
            email: 'user@example.com'
          };
        }
      }
      
      // POST /api/users/ 엔드포인트에 맞는 요청 데이터 구성
      const requestData = {
        name: userData.name || '사용자',
        auth_provider: userData.auth_provider || 'google',
        email: userData.email || "user@example.com",
        current_opic_score: profileData.currentGrade,
        target_opic_score: profileData.wishGrade,
        target_exam_date: profileData.examDate,
        background_survey: surveyData
      };
      
      console.log('저장할 통합 데이터:', requestData);
      
      // users 엔드포인트로 POST 요청
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
        throw new Error('데이터 저장에 실패했습니다: ' + errorText);
      }
      
      const result = await response.json();
      
      // 사용자 정보 업데이트
      dispatch(setUser({
        ...result,
        is_onboarded: true
      }));
      
      // 세션 스토리지 업데이트
      sessionStorage.setItem('isOnboarded', 'true');
      try {
        sessionStorage.setItem('user', JSON.stringify(result));
      } catch (e) {
        console.warn('사용자 정보 저장 실패:', e);
      }
      
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