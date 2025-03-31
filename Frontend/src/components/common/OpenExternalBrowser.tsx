import { ReactNode, useEffect } from 'react';

interface OpenExternalBrowserProps {
  children: ReactNode;
}

/**
 * 카카오톡 인앱 브라우저에서 외부 브라우저로 열기 위한 컴포넌트
 * 주로 Google 로그인과 같은 OAuth 인증이 카카오톡 인앱 브라우저에서 
 * 제대로 작동하지 않는 문제를 해결하기 위해 사용
 */
function OpenExternalBrowser({ children }: OpenExternalBrowserProps) {
  /**
   * iOS 기기인지 확인하는 함수
   */
  const isIOSAgent = (userAgent: string): boolean => {
    return /iphone|ipad|ipod/i.test(userAgent);
  };

  /**
   * 카카오톡 인앱 브라우저인지 확인하는 함수
   */
  const isKakaoTalkAgent = (userAgent: string): boolean => {
    return /kakaotalk/i.test(userAgent);
  };

  /**
   * 외부 브라우저로 URL을 여는 함수
   */
  const openKakaoTalkExternalBrowser = (url: string): void => {
    // iOS와 안드로이드를 위한 다른 처리
    if (isIOSAgent(navigator.userAgent.toLowerCase())) {
      // iOS는 kakaotalk://web/openExternal 스킴 사용
      window.location.href = `kakaotalk://web/openExternal?url=${encodeURIComponent(url)}`;
    } else {
      // 안드로이드는 intent 스킴 사용
      window.location.href = `intent://view?url=${encodeURIComponent(url)}#Intent;scheme=kakaotalk;package=com.kakao.talk;end`;
    }
  };

  /**
   * 카카오톡 인앱 브라우저를 닫는 함수
   */
  const closeKakaoTalkBrowser = (userAgent: string): void => {
    if (isIOSAgent(userAgent)) {
      // iOS는 kakaoweb://closeBrowser 스킴 사용
      window.location.href = 'kakaoweb://closeBrowser';
      return;
    }

    // 안드로이드는 kakaotalk://inappbrowser/close 스킴 사용
    window.location.href = 'kakaotalk://inappbrowser/close';
    return;
  };

  // 컴포넌트가 마운트될 때 카카오톡 인앱 브라우저 감지 및 처리
  useEffect(() => {
    // SSR 환경에서는 window와 navigator가 없으므로 체크
    if (typeof window === 'undefined' || typeof navigator === 'undefined') {
      return;
    }

    const userAgent = navigator.userAgent.toLowerCase();
    const currentUrl = window.location.href;

    // 카카오톡 인앱 브라우저인 경우 처리
    if (isKakaoTalkAgent(userAgent)) {
      // 외부 브라우저로 현재 URL 열기 시도
      openKakaoTalkExternalBrowser(currentUrl);
      
      // 외부 브라우저가 열린 후 인앱 브라우저 닫기 (지연 시간 1초)
      setTimeout(() => {
        closeKakaoTalkBrowser(userAgent);
      }, 1000);
      
      return;
    }
  }, []); // 빈 의존성 배열로 컴포넌트 마운트 시 한 번만 실행

  // children을 그대로 렌더링
  return children;
}

export default OpenExternalBrowser;