// NavigationInitializer.tsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { setNavigateFunction, setNavigateTo404Function } from '@/api/apiClient';

function NavigationInitializer() {
  const navigate = useNavigate();
  
  useEffect(() => {
    setNavigateFunction(() => navigate('/auth/login'));
    setNavigateTo404Function(() => navigate('/not-found', { replace: true }));
  }, [navigate]);
  
  return null; // 아무것도 렌더링하지 않음
}

export default NavigationInitializer;