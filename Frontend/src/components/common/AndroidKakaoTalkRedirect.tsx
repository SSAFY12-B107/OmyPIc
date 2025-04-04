import { ReactNode, useEffect } from 'react';

interface AndroidKakaoTalkRedirectProps {
  children: ReactNode;
}

/**
 * 안드로이드 카카오톡 인앱 브라우저에서 Chrome으로 리다이렉트하는 컴포넌트
 * Google 로그인 등이 카카오톡 인앱 브라우저에서 제대로 작동하지 않는 문제를 해결
 */
function AndroidKakaoTalkRedirect({ children }: AndroidKakaoTalkRedirectProps) {
  useEffect(() => {
    // SSR 환경 체크
    if (typeof window === 'undefined' || typeof navigator === 'undefined') {
      return;
    }

    const userAgent = navigator.userAgent.toLowerCase();
    const currentUrl = window.location.href;
    
    // 안드로이드 기기인지 확인
    const isAndroid = /android/i.test(userAgent);
    
    // 카카오톡 인앱 브라우저인지 확인
    const isKakaoTalk = /kakaotalk/i.test(userAgent);
    
    // 안드로이드 카카오톡 인앱 브라우저에서만 처리
    if (isAndroid && isKakaoTalk) {
      // 방법 1: 카카오톡 외부 브라우저 스킴 사용
      window.location.href = 'kakaotalk://web/openExternal?url=' + encodeURIComponent(currentUrl);
      
      // 방법 2: 크롬으로 직접 리다이렉트 (방법 1이 실패할 경우 대비)
      setTimeout(() => {
        window.location.href = 'intent://' + currentUrl.replace(/https?:\/\//i, '') + 
          '#Intent;scheme=https;package=com.android.chrome;end';
      }, 500);
    }
  }, []); // 컴포넌트 마운트 시 한 번만 실행

  return children;
}

export default AndroidKakaoTalkRedirect;