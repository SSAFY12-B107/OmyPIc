export interface ProfileData {
    wishGrade: string;
    currentGrade: string;
    examDate: string;
}
export declare const useProfile: () => {
    profileData: ProfileData;
    loading: boolean;
    error: string | null;
    fetchProfile: () => Promise<void>;
    updateProfile: (data: ProfileData) => Promise<boolean>;
    updateField: (field: keyof ProfileData, value: string) => void;
};
