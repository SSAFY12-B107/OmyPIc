// src/api/apiClient.ts
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

// 기본 설정
const BASE_URL = 'http://localhost:8000/api';

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

// 재시도 요청에 대한 타입 확장
interface RetryConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

// 응답 인터셉터 설정 수정
apiClient.interceptors.response.use(
  (response) => {
    console.log('응답 잘 감!!')
    return response;
  },
  async (error: AxiosError) => {
    if (!error.config) {
      console.log('!error.config', !error.config)
      return Promise.reject(error);
    }

    console.log('error났다', error)
    
    const originalRequest = error.config as RetryConfig;
    
    // 401 에러가 발생했을 때 및 재시도되지 않은 요청인 경우에만
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 오류 유형 확인과 함께 응답 메시지도 검사
      const errorType = error.response?.headers['x-error-type'];
      const errorData = error.response?.data as { detail?: string }; 
      const errorDetail = errorData?.detail;
      console.log('401에러 발생', error)
      console.log('errorType', errorType)
      console.log('errorDetail', errorDetail)
      console.log('header', error.response?.headers)
      
      
      // 토큰 만료 관련 오류인 경우에만 토큰 갱신 시도
      if (errorType === 'token_expired' || 
          (errorDetail && errorDetail.includes('만료된 토큰'))) {
            console.log('토큰 만료 관련 오류')
            console.log('엑세스 토큰', sessionStorage.getItem('access_token'))
        // 재시도 플래그 설정
        originalRequest._retry = true;
        
        try {
          // 토큰 갱신 요청 - 빈 객체 제거
          const response = await apiClient.post('/auth/refresh-token');
          
          // 새 액세스 토큰 저장
          const newToken = response.data.access_token;
          
          if (!newToken) {
            throw new Error('응답에 토큰이 포함되지 않았습니다');
          }
          
          setAccessToken(newToken);
          
          // 실패한 요청의 헤더에 새 토큰 설정
          originalRequest.headers.Authorization = `Bearer ${newToken}`;

          // 원래 요청 재시도
          return apiClient(originalRequest);
        } catch (refreshError) {
          // 토큰 갱신 실패 - 로그아웃 처리
          sessionStorage.removeItem('access_token');
          sessionStorage.removeItem('isOnboarded');
          
          // 알림창 표시 후 리다이렉트
          alert('토큰 갱신에 실패했습니다. 다시 로그인해주세요.');
          window.location.href = '/auth/login';
          
          return Promise.reject(refreshError);
        }
      } else {
        // 토큰 만료가 아닌 다른 모든 401 에러 - 바로 로그아웃 처리
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('isOnboarded');
        
        // 알림창 표시 후 리다이렉트
        alert('인증에 문제가 발생했습니다. 다시 로그인해주세요.');
        window.location.href = '/auth/login';
      }
    }
    
    // 다른 모든 에러
    return Promise.reject(error);
  }
);

export default apiClient;