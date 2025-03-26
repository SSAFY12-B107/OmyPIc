import { PayloadAction } from "@reduxjs/toolkit";
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
export interface TestState {
    currentTest: Test | null;
}
export declare const testActions: import("@reduxjs/toolkit").CaseReducerActions<{
    setCurrentTest: (state: import("immer").WritableDraft<TestState>, action: PayloadAction<Test>) => void;
}, "tests">;
declare const _default: import("redux").Reducer<TestState>;
export default _default;
