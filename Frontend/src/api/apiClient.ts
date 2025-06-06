import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig} from 'axios';

// 기본 설정
const BASE_URL = `${import.meta.env.VITE_API_URL}/api`;

// 로그인 페이지로 리다이렉트하는 함수 타입
type NavigateFunction = () => void;

// 기본 리다이렉트 함수
let navigateToLogin: NavigateFunction = () => {
  console.error('Navigation function not set');
};

// 외부에서 커스텀 네비게이션 함수 설정 가능
export const setNavigateFunction = (customNavigate: NavigateFunction) => {
  navigateToLogin = customNavigate;
};

// 404 페이지로 리다이렉트하는 함수 추가
let navigateTo404: NavigateFunction = () => {
  console.error('404 Navigation function not set');
};

// 외부에서 404 네비게이션 함수 설정 기능
export const setNavigateTo404Function = (customNavigate: NavigateFunction) => {
  navigateTo404 = customNavigate;
};

// Access Token을 세션 스토리지에서 가져오는 함수
const getAccessToken = (): string | null => {
  try {
    return sessionStorage.getItem('access_token');
  } catch {
    return null;
  }
};

// Access Token을 세션 스토리지에 저장하는 함수
const setAccessToken = (token: string): void => {
  try {
    sessionStorage.setItem('access_token', token);
  } catch {
    console.error('Failed to set access token');
  }
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
    return response;
  },
  async (error: AxiosError) => {
    if (!error.config) {
      console.log('!error.config', !error.config)
      return Promise.reject(error);
    }
    
    const originalRequest = error.config as RetryConfig;

    // 404 에러 처리 부분
    if (error.response?.status === 404) {
      console.error('404 Error:', error.response.data);
      
      // 그냥 존재하지 않는 경로로 리다이렉트
      // 이렇게 하면 자동으로 * 경로에 의해 NotFound 컴포넌트가 렌더링됨
      navigateTo404();
      
      return Promise.reject(error);
    }
    
    // 401 에러가 발생했을 때 및 재시도되지 않은 요청인 경우에만
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 오류 유형 확인과 함께 응답 메시지도 검사
      const errorType = error.response?.headers['x-error-type'];
      const errorData = error.response?.data as { detail?: string }; 
      const errorDetail = errorData?.detail;
      
      // 토큰 만료 관련 오류인 경우에만 토큰 갱신 시도
      if (errorType === 'token_expired' || 
          (errorDetail && errorDetail.includes('만료된 토큰'))) {

      // 로그아웃 처리 로직
      const handleLogout = () => {
        try {
          sessionStorage.removeItem('access_token');
          sessionStorage.removeItem('isOnboarded');
        } catch {
          console.error('Failed to remove tokens from session storage');
        }
        
        // 로그인 페이지로 리다이렉트
        navigateToLogin();
      };

      // AccessToken 만료 에러인 경우에만 토큰 갱신 시도
      if (errorType === 'token_expired' && originalRequest) {
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
          handleLogout();
          
          return Promise.reject(refreshError);
        }
      } else {
        // 토큰 만료가 아닌 다른 모든 401 에러 - 바로 로그아웃 처리
        handleLogout();
      }
    }
    
    // 다른 모든 에러
    return Promise.reject(error);
  }
});

export default apiClient;