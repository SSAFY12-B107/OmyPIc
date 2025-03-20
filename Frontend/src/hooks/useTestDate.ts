import { useState, useEffect } from 'react';

// 타입 정의
type TestDateResult = {
  formattedDate: string;
  dday: number;
  ddayText: string;
};

/**
 * 시험 날짜를 관리하는 커스텀 훅
 * @param isoString ISO 8601 형식의 시험 날짜 문자열
 * @returns 포맷된 날짜, D-day 숫자, D-day 텍스트
 */
export function useTestDate(isoString: string): TestDateResult {
  const [dday, setDday] = useState<number>(calculateDday(isoString));
  const formattedDate = formatTestDate(isoString);
  
  // 자정마다 D-day 업데이트
  useEffect(() => {
    const updateDday = () => {
      setDday(calculateDday(isoString));
    };
    
    // 최초 1회 실행
    updateDday();
    
    // 다음 자정에 업데이트할 타이머 설정
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(now.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);
    
    const timeUntilMidnight = tomorrow.getTime() - now.getTime();
    const timerId = setTimeout(updateDday, timeUntilMidnight);
    
    return () => clearTimeout(timerId);
  }, [isoString]);
  
  // D-day 텍스트 생성 (D-Day, D-3, D+2 등)
  const ddayText = dday === 0 ? "D-Day" : dday > 0 ? `D-${dday}` : `D+${Math.abs(dday)}`;
  
  return { formattedDate, dday, ddayText };
}

/**
 * ISO 8601 형식 날짜 문자열을 "YYYY년 M월 D일(요일) HH:MM" 형식으로 변환
 */
function formatTestDate(isoString: string): string {
  const date = new Date(isoString);
  
  // 년, 월, 일
  const year = date.getFullYear();
  const month = date.getMonth() + 1; // getMonth()는 0부터 시작
  const day = date.getDate();
  
  // 요일 (한글)
  const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
  const weekday = weekdays[date.getDay()];
  
  // 시간 (24시간 형식)
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  
  return `${year}년 ${month}월 ${day}일(${weekday}) ${hours}:${minutes}`;
}

/**
 * 시험일까지 남은 일수 계산 (D-day)
 */
function calculateDday(isoString: string): number {
  const testDate = new Date(isoString);
  const today = new Date();
  
  // 날짜 비교를 위해 시간 부분을 제거 (둘 다 자정으로 설정)
  testDate.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);
  
  // 밀리초 차이를 일수로 변환
  const diffTime = testDate.getTime() - today.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  return diffDays;
}