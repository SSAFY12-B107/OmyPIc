import React, { ReactNode } from "react";
interface HeaderContextType {
    title: string;
    setTitle: (title: string) => void;
    hideHeader: boolean;
    setHideHeader: (hide: boolean) => void;
    hideBackButton: boolean;
    setHideBackButton: (hide: boolean) => void;
    customBackAction: (() => void) | null;
    setCustomBackAction: (action: (() => void) | null) => void;
    testEndAction: (() => void) | null;
    setTestEndAction: (action: (() => void) | null) => void;
}
interface HeaderProviderProps {
    children: ReactNode;
}
export declare const HeaderProvider: React.FC<HeaderProviderProps>;
export declare const useHeader: () => HeaderContextType;
export declare const useHeaderTitle: (title: string) => void;
export declare const useHeaderBackButton: (hide?: boolean, customAction?: () => void) => void;
export declare const useHeaderVisibility: (hide?: boolean) => void;
export declare const useTestEndAction: (action: () => void) => void;
export {};
