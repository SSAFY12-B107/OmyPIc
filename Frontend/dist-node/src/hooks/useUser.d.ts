import { ProfileData } from '../store/authSlice';
export declare const useUser: () => {
    user: any;
    isAuthenticated: boolean;
    profileData: ProfileData;
    logout: () => void;
    updateProfile: (data: ProfileData) => void;
    updateProfileField: (field: keyof ProfileData, value: string) => void;
};
