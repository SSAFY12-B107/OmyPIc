export interface QuestionsResponse {
    content: string;
    questions: string[];
}
export interface CustomQuestionsRequest {
    question1: string;
    question2: string;
    question3: string;
}
export interface CreateScriptRequest {
    type: "basic" | "custom";
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
}
export interface CreateScriptResponse {
    _id: string;
    content: string;
    created_at: string;
    is_script: boolean;
}
export declare const useGetBasicQuestions: (problemId: string) => import("@tanstack/react-query").UseQueryResult<QuestionsResponse, Error>;
export declare const useGenerateCustomQuestions: () => import("@tanstack/react-query").UseMutationResult<QuestionsResponse, Error, {
    problemId: string;
    answers: CustomQuestionsRequest;
}, unknown>;
export declare const useCreateScript: () => import("@tanstack/react-query").UseMutationResult<CreateScriptResponse, Error, {
    problemId: string;
    scriptData: CreateScriptRequest;
}, unknown>;
