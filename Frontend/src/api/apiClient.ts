// src/api/apiClient.ts
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

// 기본 설정
const BASE_URL = 'http://localhost:8000/api';
const SESSION_TOKEN_KEY = 'session_token';

// Access Token을 세션 스토리지에서 가져오는 함수
const getAccessToken = (): string | null => {
  return sessionStorage.getItem('access_token');
};

// Access Token을 세션 스토리지에 저장하는 함수
const setAccessToken = (token: string): void => {
  sessionStorage.setItem('access_token', token);
};

// axios 인스턴스 생성
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // 세션 쿠키를 포함하기 위한 설정
});

// 요청 인터셉터 설정
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    
    // 토큰이 있으면 Authorization 헤더에 추가
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);
// 응답 인터셉터 설정
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config;
    
    // AccessToken 만료 에러 체크 (서버 응답에 따라 수정 필요!!)
    if (error.response?.status === 401 && originalRequest) {
      try {
        // 토큰 갱신 요청
        const response = await apiClient.post('/auth/refresh-token', {});
        
        // 새 액세스 토큰 저장
        const newToken = response.data.accessToken;
        setAccessToken(newToken);
        
        // 실패한 요청의 헤더에 새 토큰 설정
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        
        // 원래 요청 재시도
        return apiClient(originalRequest);
      } catch (refreshError) {
        // 토큰 갱신 실패 시 로그아웃 처리 등
        sessionStorage.removeItem('access_token');
        // 로그인 페이지로 리다이렉트 또는 로그아웃 이벤트 발생 등의 처리 필요
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;