export interface ProfileData {
    wishGrade: string;
    currentGrade: string;
    examDate: string;
}
export interface AuthState {
    user: any | null;
    isAuthenticated: boolean;
    profileData: ProfileData;
    loading: boolean;
    error: string | null;
}
export declare const setUser: import("@reduxjs/toolkit").ActionCreatorWithPayload<any, "auth/setUser">, clearUser: import("@reduxjs/toolkit").ActionCreatorWithoutPayload<"auth/clearUser">, setProfileField: import("@reduxjs/toolkit").ActionCreatorWithPayload<{
    field: keyof ProfileData;
    value: string;
}, "auth/setProfileField">, setProfileData: import("@reduxjs/toolkit").ActionCreatorWithPayload<ProfileData, "auth/setProfileData">, setLoading: import("@reduxjs/toolkit").ActionCreatorWithPayload<boolean, "auth/setLoading">, setError: import("@reduxjs/toolkit").ActionCreatorWithPayload<string | null, "auth/setError">;
declare const _default: import("redux").Reducer<AuthState>;
export default _default;
