import { createSlice, PayloadAction, configureStore } from "@reduxjs/toolkit";

// (응답) 테스트 타입 정의
export interface Test {
  _id: string;
  audio_s3_url?: string; // 선택적 속성으로 추가
  problem_id? : string;
  test_type: number;
  test_score: number | null;
  test_feedback: string | null;
  problem_data: {
    [key: string]: {
      problem_id: string;
      problem_category: string;
      topic_category: string;
      problem: string;
      audio_s3_url   : string;
    };
  };
}

// 테스트 배포 : 응시 횟수 제한
interface TestState {
  currentTest: Test | null;
}

const initialState: TestState = {
  currentTest: null,
};

const testSlice = createSlice({
  name: "tests",
  initialState,
  reducers: {
    setCurrentTest: (state, action: PayloadAction<Test>) => {
      state.currentTest = action.payload;
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
