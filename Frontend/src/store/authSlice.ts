import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// 프로필 데이터 타입 정의
export interface ProfileData {
  wishGrade: string;
  currentGrade: string;
  examDate: string;
}

// 인증 상태 타입 정의
export interface AuthState {
  user: any | null;
  isAuthenticated: boolean;
  profileData: ProfileData;
  loading: boolean;
  error: string | null;
}

// 초기 상태
const initialAuthState: AuthState = {
  user: null,
  isAuthenticated: false,
  profileData: {
    wishGrade: '',
    currentGrade: '',
    examDate: ''
  },
  loading: false,
  error: null
};

// Auth 슬라이스 생성
const authSlice = createSlice({
  name: 'auth',
  initialState: initialAuthState,
  reducers: {
    setUser: (state, action: PayloadAction<any>) => {
      state.user = action.payload;
      state.isAuthenticated = true;
    },
    clearUser: (state) => {
      state.user = null;
      state.isAuthenticated = false;
    },
    setProfileField: (state, action: PayloadAction<{ field: keyof ProfileData; value: string }>) => {
      const { field, value } = action.payload;
      state.profileData[field] = value;
    },
    setProfileData: (state, action: PayloadAction<ProfileData>) => {
      state.profileData = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    }
  }
});

// 액션 생성자 내보내기
export const { 
  setUser, 
  clearUser, 
  setProfileField, 
  setProfileData, 
  setLoading, 
  setError 
} = authSlice.actions;

// 리듀서 내보내기
export default authSlice.reducer;