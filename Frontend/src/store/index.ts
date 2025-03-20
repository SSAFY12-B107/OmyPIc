import { createSlice, PayloadAction, configureStore } from "@reduxjs/toolkit";

// (응답) 테스트 타입 정의
export interface Test {
  _id: string;
  test_type: boolean;
  test_score: number | null;
  test_feedback: string | null;
  problem_data: {
    [key: string]: {
      problem_id: string;
      problem_category: string;
      topic_category: string;
      problem: string;
    };
  };
}

// 테스트 배포 : 응시 횟수 제한
interface TestState {
  currentTest: Test | null;
  usageCount: number;
  maxUsageCount: number;
  lastResetDate: string; // 마지막 리셋 날짜를 저장 // 횟수 제한
}

const initialState: TestState = {
  currentTest: null,
  usageCount: 0,
  maxUsageCount: 3,
  lastResetDate: new Date().toISOString().split("T")[0], // YYYY-MM-DD 형식
};

const testSlice = createSlice({
  name: "tests",
  initialState,
  reducers: {
    setCurrentTest: (state, action: PayloadAction<Test>) => {
      state.currentTest = action.payload;
    },

    incrementUsageCount: (state) => {
      // 현재 날짜와 마지막 리셋 날짜를 비교
      const today = new Date().toISOString().split("T")[0];
      if (today !== state.lastResetDate) {
        // 날짜가 변경되었으면 카운트 리셋
        state.usageCount = 1; // 증가 후 값이므로 1로 설정
        state.lastResetDate = today;
      } else {
        // 같은 날이면 카운트 증가
        state.usageCount += 1;
      }
    },
    // 하루 지나면 0으로 리셋 설정 필요
    resetUsageCount: (state) => {
      state.usageCount = 0;
    },
  },
});

const store = configureStore({
  reducer: { tests: testSlice.reducer },
});

// 자동으로 액션 (생성자 생성 -> 자동으로 type 전달
export const testActions = testSlice.actions;

// 타입 안정성
// 1) store 타입 정의(useSelector로 타페이지에서 활용할 때 타입 수동 지정 해결 위함)
export type RootState = ReturnType<typeof store.getState>;
// 2) 비동기 액션 dispatch 타입 정의
export type AppDispatch = typeof store.dispatch;

export default store;
