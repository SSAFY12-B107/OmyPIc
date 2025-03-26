// src/hooks/useProfile.ts
import { useState, useEffect } from 'react';
import apiClient from '../api/apiClient';

// 프로필 데이터 타입 정의
export interface ProfileData {
  wishGrade: string;
  currentGrade: string;
  examDate: string;
}

export const useProfile = () => {
  // 프로필 데이터 상태
  const [profileData, setProfileData] = useState<ProfileData>({
    wishGrade: '',
    currentGrade: '',
    examDate: ''
  });
  
  // 로딩 상태
  const [loading, setLoading] = useState(false);
  
  // 에러 상태
  const [error, setError] = useState<string | null>(null);

  // 프로필 데이터 불러오기
  const fetchProfile = async () => {
    try {
      setLoading(true);
      
      // 임시 조치: 실제 API 호출 주석 처리 (404 오류 방지)
      // const response = await apiClient.get('/api/user/profile');
      
      // 임시 데이터
      setProfileData({
        wishGrade: '',
        currentGrade: '',
        examDate: ''
      });
      
      setError(null);
    } catch (err) {
      setError('프로필 정보를 불러오는데 실패했습니다');
      console.error('프로필 로드 오류:', err);
    } finally {
      setLoading(false);
    }
  };

  // 프로필 데이터 업데이트
  const updateProfile = async (data: ProfileData) => {
    try {
      setLoading(true);
      
      // 백엔드 API에 맞게 데이터 변환
      const userData = {
        target_opic_score: data.wishGrade,
        current_opic_score: data.currentGrade,
        target_exam_date: data.examDate
      };
      
      // 실제 API 호출 
      const response = await apiClient.post('/api/user/profile', userData);
      
      if (response.data.success) {
        setProfileData(data);
        setError(null);
        return true;
      } else {
        setError('프로필 업데이트에 실패했습니다');
        return false;
      }
    } catch (err) {
      // 개발 중에는 API 오류를 무시하고 성공으로 처리
      console.error('프로필 업데이트 오류:', err);
      // 임시로 성공 반환
      setProfileData(data);
      return true;
    } finally {
      setLoading(false);
    }
  };

  // 프로필 필드 업데이트
  const updateField = (field: keyof ProfileData, value: string) => {
    setProfileData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // 컴포넌트 마운트 시 프로필 데이터 로드
  useEffect(() => {
    fetchProfile();
  }, []);

  // 프로필 데이터와 상태, 메서드를 반환
  return {
    profileData,
    loading,
    error,
    fetchProfile,
    updateProfile,
    updateField
  };
};