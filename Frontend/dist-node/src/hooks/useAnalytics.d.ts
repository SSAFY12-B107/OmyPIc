export declare const useAnalytics: () => {
    initGA: () => void;
    logPageView: (path: string, customParams?: Record<string, any>) => void;
    logEvent: (category: string, action: string, label?: string, value?: number) => void;
    logExit: (action: string, label?: string, value?: number) => void;
    setUserProperties: (userProperties: Record<string, any>) => void;
};
export declare const useRouteChangeTracking: () => void;
