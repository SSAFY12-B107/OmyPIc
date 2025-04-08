import { PayloadAction } from "@reduxjs/toolkit";
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
export interface TestState {
    currentTest: Test | null;
    currentSingleProblem: SingleProblem | null;
    isRandomProblem: boolean;
}
export declare const testActions: import("@reduxjs/toolkit").CaseReducerActions<{
    setCurrentTest: (state: import("immer").WritableDraft<TestState>, action: PayloadAction<Test | SingleProblem>) => void;
}, "tests">;
declare const _default: import("redux").Reducer<TestState>;
export default _default;
