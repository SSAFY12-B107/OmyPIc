export interface SurveyData {
    profession: string | number;
    is_student: boolean;
    studied_lecture: string | number;
    living_place: string | number;
    info: (string | number)[];
}
export declare const useSurvey: () => {
    saveProfileAndSurvey: (surveyData: SurveyData) => Promise<{
        success: boolean;
        data: any;
        error?: undefined;
    } | {
        success: boolean;
        error: string;
        data?: undefined;
    }>;
    isSaving: boolean;
};
