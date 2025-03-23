import { createSlice, PayloadAction, createSelector } from "@reduxjs/toolkit";

// 질문 단계 수
export const TOTAL_STEPS = 3;

// 상태 타입 정의
export interface ScriptState {
  content: string; // 문제
  questions: string[]; // (기본 or 꼬리) 질문들의 배열
  currentStep: number; // 현재 단계 (1, 2, 3)
  basicAnswers: string[]; // 기본 질문에 대한 답변들의 배열
  customAnswers: string[]; // 꼬리 질문에 대한 답변들의 배열
  isCustomMode: boolean; // 현재 모드 (false: 기본 질문 모드, true: 꼬리 질문 모드)
}

// 초기 상태
const initialState: ScriptState = {
  content: "",
  questions: [],
  currentStep: 1,
  basicAnswers: ["", "", ""],
  customAnswers: ["", "", ""],
  isCustomMode: false,
};

// Slice 생성
const scriptSlice = createSlice({
  name: "script",
  initialState,
  reducers: {
    // 컨텐츠 설정
    setContent(state, action: PayloadAction<string>) {
      state.content = action.payload;
    },
    
    // 질문 설정
    setQuestions(state, action: PayloadAction<string[]>) {
      state.questions = action.payload;
    },
    
    // 현재 단계 설정
    setCurrentStep(state, action: PayloadAction<number>) {
      state.currentStep = action.payload;
    },
    
    // 다음 단계로 이동
    nextStep(state) {
      if (state.currentStep < TOTAL_STEPS) {
        state.currentStep += 1;
      }
    },
    
    // 이전 단계로 이동
    prevStep(state) {
      if (state.currentStep > 1) {
        state.currentStep -= 1;
      }
    },
    
    // 현재 모드에 따른 답변 설정
    setCurrentAnswer(state, action: PayloadAction<{ index: number; value: string }>) {
      const { index, value } = action.payload;
      if (state.isCustomMode) {
        if (index >= 0 && index < state.customAnswers.length) {
          state.customAnswers[index] = value;
        }
      } else {
        if (index >= 0 && index < state.basicAnswers.length) {
          state.basicAnswers[index] = value;
        }
      }
    },
    
    // 현재 모드 설정 (기본/꼬리)
    setIsCustomMode(state, action: PayloadAction<boolean>) {
      state.isCustomMode = action.payload;
    },
    
    // 상태 초기화
    clearScriptState() {
      return initialState;
    },
  },
});

export const {
  setContent,
  setQuestions,
  setCurrentStep,
  nextStep,
  prevStep,
  setCurrentAnswer,
  setIsCustomMode,
  clearScriptState,
} = scriptSlice.actions;

// 현재 모드에 따른 답변 목록 가져오기 셀렉터 (메모이제이션 적용)
export const getCurrentAnswers = createSelector(
  (state: { script: ScriptState }) => state.script.isCustomMode,
  (state: { script: ScriptState }) => state.script.basicAnswers,
  (state: { script: ScriptState }) => state.script.customAnswers,
  (isCustomMode, basicAnswers, customAnswers) => 
    isCustomMode ? customAnswers : basicAnswers
);

// API 요청 데이터 형식으로 변환하는 셀렉터 (메모이제이션 적용)
export const getScriptRequestData = createSelector(
  (state: { script: ScriptState }) => state.script.isCustomMode,
  (state: { script: ScriptState }) => state.script.basicAnswers,
  (state: { script: ScriptState }) => state.script.customAnswers,
  (isCustomMode, basicAnswers, customAnswers) => ({
    type: isCustomMode ? "custom" : "basic",
    basic_answers: {
      answer1: basicAnswers[0] || '',
      answer2: basicAnswers[1] || '',
      answer3: basicAnswers[2] || ''
    },
    custom_answers: {
      answer1: customAnswers[0] || '',
      answer2: customAnswers[1] || '',
      answer3: customAnswers[2] || ''
    }
  })
);

export default scriptSlice.reducer;