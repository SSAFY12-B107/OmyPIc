export interface Problem {
    _id: string;
    topic_category: string;
    problem_category: string;
    content: string;
}
export interface ProblemDetail {
    problem: {
        _id: string;
        content: string;
    };
    user_scripts: any[];
    test_notes: any[];
    script_limit: {
        used: number;
        limit: number;
        remaining: number;
    };
}
export interface ProblemQueryParams {
    skip: number;
    limit: number;
}
export declare const useGetProblems: (category: string) => import("@tanstack/react-query").UseInfiniteQueryResult<import("@tanstack/query-core").InfiniteData<Problem[], unknown>, Error>;
export declare const useGetProblemDetail: (problem_id: string) => import("@tanstack/react-query").UseQueryResult<ProblemDetail, Error>;
