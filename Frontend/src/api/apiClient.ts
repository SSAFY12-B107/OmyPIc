// src/api/apiClient.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// 기본 설정
const BASE_URL = 'https://localhost:5173';
const SESSION_TOKEN_KEY = 'session_token';

// axios 인스턴스 생성
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // 세션 쿠키를 포함하기 위한 설정
});

/**
 * 세션 토큰 저장
 */
export const setSessionToken = (token: string): void => {
  localStorage.setItem(SESSION_TOKEN_KEY, token);
};

/**
 * 세션 토큰 조회
 */
export const getSessionToken = (): string | null => {
  return localStorage.getItem(SESSION_TOKEN_KEY);
};

/**
 * 세션 토큰 제거 (로그아웃)
 */
export const clearSessionToken = (): void => {
  localStorage.removeItem(SESSION_TOKEN_KEY);
};

// 요청 인터셉터 - 세션 토큰 자동 주입
apiClient.interceptors.request.use(
  (config) => {
    const sessionToken = getSessionToken();
    if (sessionToken) {
      config.headers['X-Session-Token'] = sessionToken;
      // 또는 다른 세션 토큰 헤더 형식 사용
      // config.headers['Session-Token'] = sessionToken;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 - 에러 처리 및 세션 만료 대응
apiClient.interceptors.response.use(
  (response) => {
    // 응답에서 세션 토큰이 포함되어 있다면 저장
    const newSessionToken = response.headers['x-session-token'];
    if (newSessionToken) {
      setSessionToken(newSessionToken);
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // 401 에러(인증 실패) 또는 403 에러(세션 만료) 처리
    if ((error.response?.status === 401 || error.response?.status === 403) && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // 세션이 만료된 경우 로그아웃 처리
      clearSessionToken();
      
      // 로그인 페이지로 리다이렉트
      window.location.href = '/login';
      return Promise.reject(error);
    }
    
    return Promise.reject(error);
  }
);

// API 클라이언트 타입 정의
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  message: string;
  success: boolean;
}

// API 요청 함수들
export const apiService = {
  get: <T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => 
    apiClient.get<ApiResponse<T>>(url, config),
    
  post: <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => 
    apiClient.post<ApiResponse<T>>(url, data, config),
    
  put: <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => 
    apiClient.put<ApiResponse<T>>(url, data, config),
    
  delete: <T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => 
    apiClient.delete<ApiResponse<T>>(url, config),
    
  patch: <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => 
    apiClient.patch<ApiResponse<T>>(url, data, config),
};

/**
 * 로그인 함수 - 세션 토큰을 설정
 * @param sessionToken 서버에서 받은 세션 토큰
 */
export const login = (sessionToken: string): void => {
  setSessionToken(sessionToken);
};

/**
 * 로그아웃 함수 - 세션 토큰을 제거하고 서버에 로그아웃 요청
 */
export const logout = async (): Promise<void> => {
  try {
    // 서버에 로그아웃 요청 (선택적)
    await apiClient.post('/auth/logout');
  } catch (error) {
    console.error('로그아웃 API 호출 실패:', error);
  } finally {
    // 로컬 세션 토큰 제거
    clearSessionToken();
  }
};

export default apiClient;