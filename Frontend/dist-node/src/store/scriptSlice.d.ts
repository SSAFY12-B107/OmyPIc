export declare const TOTAL_STEPS = 3;
export interface ScriptState {
    content: string;
    questions: string[];
    currentStep: number;
    basicAnswers: string[];
    customAnswers: string[];
    isCustomMode: boolean;
}
export declare const setContent: import("@reduxjs/toolkit").ActionCreatorWithPayload<string, "script/setContent">, setQuestions: import("@reduxjs/toolkit").ActionCreatorWithPayload<string[], "script/setQuestions">, setCurrentStep: import("@reduxjs/toolkit").ActionCreatorWithPayload<number, "script/setCurrentStep">, nextStep: import("@reduxjs/toolkit").ActionCreatorWithoutPayload<"script/nextStep">, prevStep: import("@reduxjs/toolkit").ActionCreatorWithoutPayload<"script/prevStep">, setCurrentAnswer: import("@reduxjs/toolkit").ActionCreatorWithPayload<{
    index: number;
    value: string;
}, "script/setCurrentAnswer">, setIsCustomMode: import("@reduxjs/toolkit").ActionCreatorWithPayload<boolean, "script/setIsCustomMode">, clearScriptState: import("@reduxjs/toolkit").ActionCreatorWithoutPayload<"script/clearScriptState">;
export declare const getCurrentAnswers: ((state: {
    script: ScriptState;
} & {
    script: ScriptState;
} & {
    script: ScriptState;
}) => string[]) & {
    clearCache: () => void;
    resultsCount: () => number;
    resetResultsCount: () => void;
} & {
    resultFunc: (resultFuncArgs_0: boolean, resultFuncArgs_1: string[], resultFuncArgs_2: string[]) => string[];
    memoizedResultFunc: ((resultFuncArgs_0: boolean, resultFuncArgs_1: string[], resultFuncArgs_2: string[]) => string[]) & {
        clearCache: () => void;
        resultsCount: () => number;
        resetResultsCount: () => void;
    };
    lastResult: () => string[];
    dependencies: [(state: {
        script: ScriptState;
    }) => boolean, (state: {
        script: ScriptState;
    }) => string[], (state: {
        script: ScriptState;
    }) => string[]];
    recomputations: () => number;
    resetRecomputations: () => void;
    dependencyRecomputations: () => number;
    resetDependencyRecomputations: () => void;
} & {
    argsMemoize: typeof import("reselect").weakMapMemoize;
    memoize: typeof import("reselect").weakMapMemoize;
};
export declare const getScriptRequestData: ((state: {
    script: ScriptState;
} & {
    script: ScriptState;
} & {
    script: ScriptState;
}) => {
    type: string;
    basic_answers: {
        answer1: string;
        answer2: string;
        answer3: string;
    };
    custom_answers: {
        answer1: string;
        answer2: string;
        answer3: string;
    };
}) & {
    clearCache: () => void;
    resultsCount: () => number;
    resetResultsCount: () => void;
} & {
    resultFunc: (resultFuncArgs_0: boolean, resultFuncArgs_1: string[], resultFuncArgs_2: string[]) => {
        type: string;
        basic_answers: {
            answer1: string;
            answer2: string;
            answer3: string;
        };
        custom_answers: {
            answer1: string;
            answer2: string;
            answer3: string;
        };
    };
    memoizedResultFunc: ((resultFuncArgs_0: boolean, resultFuncArgs_1: string[], resultFuncArgs_2: string[]) => {
        type: string;
        basic_answers: {
            answer1: string;
            answer2: string;
            answer3: string;
        };
        custom_answers: {
            answer1: string;
            answer2: string;
            answer3: string;
        };
    }) & {
        clearCache: () => void;
        resultsCount: () => number;
        resetResultsCount: () => void;
    };
    lastResult: () => {
        type: string;
        basic_answers: {
            answer1: string;
            answer2: string;
            answer3: string;
        };
        custom_answers: {
            answer1: string;
            answer2: string;
            answer3: string;
        };
    };
    dependencies: [(state: {
        script: ScriptState;
    }) => boolean, (state: {
        script: ScriptState;
    }) => string[], (state: {
        script: ScriptState;
    }) => string[]];
    recomputations: () => number;
    resetRecomputations: () => void;
    dependencyRecomputations: () => number;
    resetDependencyRecomputations: () => void;
} & {
    argsMemoize: typeof import("reselect").weakMapMemoize;
    memoize: typeof import("reselect").weakMapMemoize;
};
declare const _default: import("redux").Reducer<ScriptState>;
export default _default;
