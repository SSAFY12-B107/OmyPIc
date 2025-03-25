export interface Scores {
    total_score: string | null;
    comboset_score: string | null;
    roleplaying_score: string | null;
    unexpected_score: string | null;
}
export interface TestHistory {
    id: string;
    overall_feedback_status: string;
    test_date: string;
    test_type: boolean;
    test_score: Scores | null;
}
export interface AverageScore {
    total_score: string | null;
    comboset_score: string | null;
    roleplaying_score: string | null;
    unexpected_score: string | null;
}
export interface UserHistoryResponse {
    average_score: AverageScore;
    test_history: TestHistory[];
    test_counts: {
        test_count: {
            used: number;
            limit: number;
            remaining: number;
        };
        random_problem: {
            used: number;
            limit: number;
            remaining: number;
        };
    };
}
export declare const useUserHistory: () => import("@tanstack/react-query").UseQueryResult<UserHistoryResponse, Error>;
