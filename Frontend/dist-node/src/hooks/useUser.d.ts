import { ProfileData } from '../store/authSlice';
interface ErrorResponse {
    detail?: string;
    [key: string]: any;
}
export declare const useUser: () => {
    user: any;
    isAuthenticated: boolean;
    profileData: ProfileData;
    isSubmitting: boolean;
    checkAuth: () => Promise<boolean>;
    logout: () => void;
    updateProfile: (data: ProfileData) => void;
    updateProfileField: (field: keyof ProfileData, value: string) => void;
    saveProfile: () => Promise<{
        success: boolean;
        data: unknown;
        error?: undefined;
    } | {
        success: boolean;
        error: string;
        data?: undefined;
    }>;
    createUserProfile: (profileWithSurvey: any) => Promise<{
        success: boolean;
        data: ErrorResponse;
        error?: undefined;
    } | {
        success: boolean;
        error: string;
        data?: undefined;
    }>;
    saveProfileAndSurvey: (surveyData: any) => Promise<{
        success: boolean;
        data: ErrorResponse;
        error?: undefined;
    } | {
        success: boolean;
        error: string;
        data?: undefined;
    }>;
};
export {};
