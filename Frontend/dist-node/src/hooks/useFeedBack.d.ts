export interface MultipleFeedback {
    total_feedback: string;
    paragraph: string;
    vocabulary: string;
    spoken_amount: string;
}
export interface SingleFeedback {
    paragraph: string;
    vocabulary: string;
    spoken_amount: string;
}
export interface ProblemData {
    problem_id: string;
    problem_category: string;
    topic_category: string;
    problem: string;
    user_response: string | null;
    score: string | null;
    feedback: SingleFeedback | null;
}
export interface TestFeedbackData {
    _id: string;
    user_id: string;
    test_type: boolean;
    test_date: string;
    test_score: {
        total_score: string | null;
        comboset_score: string | null;
        roleplaying_score: string | null;
        unexpected_score: string | null;
    };
    test_feedback: MultipleFeedback | null;
    problem_data: {
        [key: string]: ProblemData;
    };
}
export declare const useFeedback: (test_pk: string | undefined) => import("@tanstack/react-query").UseQueryResult<TestFeedbackData, Error>;
export declare const getProblemData: (feedbackData: TestFeedbackData | undefined, problemNumber: number) => ProblemData | undefined;
export declare const getTotalProblems: (feedbackData: TestFeedbackData | undefined) => number;
