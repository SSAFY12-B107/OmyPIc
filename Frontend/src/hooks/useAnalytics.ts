// src/hooks/useAnalytics.ts
import { useEffect, useCallback, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import ReactGA from 'react-ga4';

// 환경변수에서 GA 측정 ID 가져오기
const TRACKING_ID = import.meta.env.VITE_GA_TRACKING_ID;

export const useAnalytics = () => {
  // GA 초기화 함수
  const initGA = useCallback(() => {
    if (!TRACKING_ID) {
      console.warn('Google Analytics Tracking ID not found in environment variables');
      return;
    }

    if (process.env.NODE_ENV === 'production') {
      ReactGA.initialize(TRACKING_ID);
      console.log('GA initialized in production mode');
    } else {
      // 개발 환경에서도 GA 초기화를 원한다면 아래 주석을 해제하세요
      // ReactGA.initialize(TRACKING_ID, { testMode: true });
      console.log('GA not initialized in development mode');
    }
  }, []);

  // 페이지 뷰 추적
  const logPageView = useCallback((path: string) => {
    const page = path || '';
    ReactGA.send({ hitType: 'pageview', page });
    console.log(`Logged pageview for: ${page}`);
  }, []);

  // 사용자 이벤트 추적
  const logEvent = useCallback((category: string, action: string, label?: string, value?: number) => {
    ReactGA.event({
      category,
      action,
      label,
      value
    });
    console.log(`Logged event: ${category} - ${action} - ${label} - ${value}`);
  }, []);

  // 이탈 이벤트 추적
  const logExit = useCallback((action: string, label?: string, value?: number) => {
    ReactGA.event({
      category: 'Exit',
      action,
      label,
      value
    });
    console.log(`Logged exit event: ${action} - ${label} - ${value}`);
  }, []);

  // 사용자 정보 설정
  const setUserProperties = useCallback((userProperties: Record<string, any>) => {
    ReactGA.set(userProperties);
    console.log('User properties set:', userProperties);
  }, []);

  return {
    initGA,
    logPageView,
    logEvent,
    logExit,
    setUserProperties
  };
};

// 라우트 변경 추적 훅
export const useRouteChangeTracking = () => {
  const { logPageView, logExit } = useAnalytics();
  const location = useLocation();
  const prevPathRef = useRef<string>('');
  const entryTimeRef = useRef<number>(Date.now());
  
  useEffect(() => {
    const currentPath = location.pathname + location.search;
    const prevPath = prevPathRef.current;
    
    if (prevPath && prevPath !== currentPath) {
      // 이전 페이지에서의 체류 시간 계산
      const timeSpent = Date.now() - entryTimeRef.current;
      
      // 페이지 이탈 이벤트 추적
      logExit('Page Navigation', prevPath, Math.floor(timeSpent / 1000));
    }
    
    // 현재 페이지 진입 시간 및 경로 업데이트
    entryTimeRef.current = Date.now();
    prevPathRef.current = currentPath;
    
    // 페이지 뷰 이벤트 추적
    logPageView(currentPath);
  }, [location, logPageView, logExit]);
};