// src/components/common/RouteTracker.tsx
import { useRouteChangeTracking } from "../../hooks/useAnalytics";

const RouteTracker = () => {
  // 라우트 변경 추적 훅 사용
  useRouteChangeTracking();
  
  // 이 컴포넌트는 UI를 렌더링하지 않고 추적 기능만 수행
  return null;
};

export default RouteTracker;