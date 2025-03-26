interface BackgroundSurvey {
    profession: number;
    is_student: boolean;
    studied_lecture: number;
    living_place: number;
    info: string[];
}
interface UserInfo {
    _id: string;
    name: string;
    email: string;
    current_opic_score: string;
    target_opic_score: string;
    target_exam_date: string;
    is_onboarded: boolean;
    background_survey: BackgroundSurvey;
    test: {
        test_date: (string | null)[];
        test_score: (string | null)[];
    };
}
export declare const useGetUserInfo: () => import("@tanstack/react-query").UseQueryResult<UserInfo, Error>;
export declare const useLogout: () => import("@tanstack/react-query").UseMutationResult<import("axios").AxiosResponse<any, any>, Error, void, unknown>;
export {};
