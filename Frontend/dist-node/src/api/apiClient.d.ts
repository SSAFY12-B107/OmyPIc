import { AxiosInstance } from 'axios';
type NavigateFunction = () => void;
export declare const setNavigateFunction: (customNavigate: NavigateFunction) => void;
declare const apiClient: AxiosInstance;
export default apiClient;
