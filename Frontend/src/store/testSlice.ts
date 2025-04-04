import { createSlice, PayloadAction } from "@reduxjs/toolkit";

// 단일 문제에 대한 인터페이스 (test_type === 2)
export interface SingleProblem {
  test_id: string;
  problem_id: string;
  problem_category: string;
  topic_category: string;
  content: string;
  audio_s3_url: string;
  high_grade_kit: boolean;
  user_id: string;
}

// 다른 테스트 타입에 대한 인터페이스
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
      processing_status?: string;
      processing_message?: string;
    };
  };
}

// 테스트 상태 타입
export interface TestState {
  currentTest: Test | null;
  currentSingleProblem: SingleProblem | null;
  isRandomProblem: boolean;
}

const initialState: TestState = {
  currentTest: null,
  currentSingleProblem: null,
  isRandomProblem: false
};

const testSlice = createSlice({
  name: "tests",
  initialState,
  reducers: {
    setCurrentTest: (state, action: PayloadAction<Test | SingleProblem>) => {
      // test_type이 2인 경우 (단일 문제)
      if ('test_id' in action.payload) {
        state.currentSingleProblem = action.payload;
        state.currentTest = null;
        state.isRandomProblem = true;
      } 
      // 다른 test_type인 경우
      else {
        state.currentTest = action.payload as Test;
        state.currentSingleProblem = null;
        state.isRandomProblem = false;
      }
    },
  },
});

// 액션들 내보내기
export const testActions = testSlice.actions;

// 리듀서 내보내기
export default testSlice.reducer;