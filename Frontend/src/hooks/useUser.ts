import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { 
  clearUser, 
  setProfileData,
  setProfileField,
  ProfileData
} from '../store/authSlice';

export const useUser = () => {
  const dispatch = useDispatch();
  const { user, isAuthenticated, profileData } = useSelector((state: RootState) => state.auth);

  // 로그아웃
  const logout = () => {
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

  return {
    user,
    isAuthenticated,
    profileData,
    logout,
    updateProfile,
    updateProfileField,
  };
};