// src/hooks/useAnalytics.ts
declare const document: Document;

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

  // 페이지 뷰 추적 (커스텀 파라미터 지원 추가)
  const logPageView = useCallback((path: string, customParams?: Record<string, any>) => {
    const page = path || '';
    ReactGA.send({ 
      hitType: 'pageview', 
      page,
      ...customParams
    });
    console.log(`Logged pageview for: ${page}`, customParams);
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
  const { logPageView, logEvent, logExit } = useAnalytics();
  const location = useLocation();
  const prevPathRef = useRef<string>('');
  const entryTimeRef = useRef<number>(Date.now());
  const referrerRef = useRef<string>('');
  
  // 동적 라우트 패턴을 정규화하는 함수
  const getNormalizedPath = (path: string): string => {
    // 경로 패턴 정규화 규칙
    const normalizePatterns = [
      // scripts/:category/:problemId 패턴을 '/scripts/[category]/[problemId]'로 정규화
      { pattern: /^\/scripts\/[^\/]+\/[^\/]+$/, normalized: '/scripts/[category]/[problemId]' },
      // scripts/:category/:problemId/write 패턴을 '/scripts/[category]/[problemId]/write'로 정규화
      { pattern: /^\/scripts\/[^\/]+\/[^\/]+\/write$/, normalized: '/scripts/[category]/[problemId]/write' },
      // scripts/:category 패턴을 '/scripts/[category]'로 정규화
      { pattern: /^\/scripts\/[^\/]+$/, normalized: '/scripts/[category]' },
      // tests/feedback/:test_pk 패턴을 '/tests/feedback/[test_pk]'로 정규화
      { pattern: /^\/tests\/feedback\/[^\/]+$/, normalized: '/tests/feedback/[test_pk]' },
    ];

    // 현재 경로가 정규화 패턴과 일치하는지 확인
    for (const { pattern, normalized } of normalizePatterns) {
      if (pattern.test(path)) {
        return normalized;
      }
    }

    // 일치하는 패턴이 없으면 원래 경로 반환
    return path;
  };
  
  // 경로에 따른 타이틀 매핑
  const getPageTitle = (path: string): string => {
    const titleMappings: Record<string, string> = {
      '/': '홈',
      '/home': '마이페이지',
      '/tests': '실전연습 메인',
      '/tests/practice': '실전연습 진행',
      '/tests/feedback/[test_pk]': '실전연습 피드백',
      '/scripts': '스크립트 메인',
      '/scripts/[category]': '스크립트 리스트',
      '/scripts/[category]/[problemId]': '스크립트 상세',
      '/scripts/[category]/[problemId]/write': '스크립트 작성',
      '/auth/survey': 'background survey',
      '/auth/profile': '회원정보 입력',
      '/auth/login': '로그인',
      '/callback': '로그인 콜백'
    };
    
    const normalizedPath = getNormalizedPath(path);
    return titleMappings[normalizedPath] || '페이지 제목 없음';
  };
  
  useEffect(() => {
    // 처음 진입 시에만 레퍼러 정보 저장
    if (!prevPathRef.current) {
      const documentReferrer = (document as any).referrer;
      if (documentReferrer) {
        referrerRef.current = documentReferrer;
        // 외부 레퍼러 정보 이벤트 기록
        logEvent('Referrer', 'External Visit', documentReferrer);
      }
    }
    
    const currentPath = location.pathname + location.search;
    const normalizedPath = getNormalizedPath(currentPath);
    const prevPath = prevPathRef.current;
    const pageTitle = getPageTitle(currentPath);
    
    if (prevPath && prevPath !== normalizedPath) {
      // 이전 페이지에서의 체류 시간 계산
      const timeSpent = Date.now() - entryTimeRef.current;
      
      // 페이지 이탈 이벤트 추적
      logExit('Page Navigation', prevPath, Math.floor(timeSpent / 1000));
      
      // 내부 페이지 간 이동 추적 (레퍼러로 기록)
      logEvent('Referrer', 'Internal Navigation', `${prevPath} -> ${normalizedPath}`);
    }
    
    // 현재 페이지 진입 시간 및 경로 업데이트
    entryTimeRef.current = Date.now();
    prevPathRef.current = normalizedPath;
    
    // 페이지 뷰 이벤트 추적 (페이지 타이틀 포함)
    logPageView(normalizedPath, {
      page_title: pageTitle
    });
    
  }, [location, logPageView, logEvent, logExit]);
};