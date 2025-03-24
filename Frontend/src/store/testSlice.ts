import { createSlice, PayloadAction } from "@reduxjs/toolkit";

// (응답) 테스트 타입 정의
export interface Test {
  _id: string;
  audio_s3_url?: string;
  problem_id?: string;
  test_type: number;
  test_score: number | null;
  test_feedback: string | null;
  problem_data: {
    [key: string]: {
      problem_id: string;
      problem_category: string;
      topic_category: string;
      problem: string;
      audio_s3_url: string;
    };
  };
}

// 테스트 상태 타입
export interface TestState {
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

// 액션들 내보내기
export const testActions = testSlice.actions;

// 리듀서 내보내기
export default testSlice.reducer;