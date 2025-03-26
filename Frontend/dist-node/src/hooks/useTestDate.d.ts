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
export declare function useTestDate(isoString: string): TestDateResult;
export {};
