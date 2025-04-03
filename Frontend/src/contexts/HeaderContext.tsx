import React, {
  createContext,
  useContext,
  ReactNode,
  useState,
  useEffect,
  useMemo,
} from "react";

import { useLocation, useNavigate } from "react-router-dom";

// 헤더가 필요한 경로 목록 (여기에 헤더가 표시되어야 하는 경로만 나열)
const HEADER_VISIBLE_PATHS = [
  "/tests", 
  "/tests/practice", 
  "/tests/feedback", 
  "/scripts",
  "/auth/survey",
  "/auth/profile"
];

interface HeaderContextType {
  title: string;
  setTitle: (title: string) => void;
  hideHeader: boolean;
  setHideHeader: (hide: boolean) => void;
  hideBackButton: boolean;
  setHideBackButton: (hide: boolean) => void;
  customBackAction: (() => void) | null;
  setCustomBackAction: (action: (() => void) | null) => void;
  testEndAction: (() => void) | null; // 테스트 종료 처리 함수
  setTestEndAction: (action: (() => void) | null) => void; // 테스트 종료 함수 설정
}

const HeaderContext = createContext<HeaderContextType | undefined>(undefined);

interface HeaderProviderProps {
  children: ReactNode;
}

export const HeaderProvider: React.FC<HeaderProviderProps> = ({ children }) => {
  const [title, setTitle] = useState<string>("");
  const [hideHeader, setHideHeader] = useState<boolean>(false);
  const [hideBackButton, setHideBackButton] = useState<boolean>(false);
  const [customBackAction, setCustomBackAction] = useState<(() => void) | null>(
    null
  );
  const [testEndAction, setTestEndAction] = useState<(() => void) | null>(null); // 테스트 관련 상태

  const location = useLocation();
  const navigate = useNavigate();

  // 경로가 변경될 때 자동으로 헤더 상태 초기화
  useEffect(() => {
    // 현재 경로가 헤더가 필요한 경로 목록에 포함되어 있는지 확인
    const isHeaderVisible = HEADER_VISIBLE_PATHS.some(
      (path) => location.pathname.startsWith(path)
    );
    
    // 헤더가 필요한 경로가 아니면 숨김
    setHideHeader(!isHeaderVisible);

    // 뒤로가기 버튼이 필요없는 경로인지 확인
    const paths = ["/auth/survey", "/auth/profile", "/tests", "/scripts"];
    const shouldHideBackButton = paths.some(
      (path) => location.pathname === path
    );
    setHideBackButton(shouldHideBackButton);

    // 커스텀 백 액션 초기화 및 설정
    const pathParts = location.pathname.split("/");

    if (pathParts.length === 5 && pathParts[4] === "write") {
      setCustomBackAction(null);
    } else if (pathParts[1] === "scripts") {
      let backPath = "/scripts"; // 기본적으로 /scripts로 이동

      if (pathParts.length === 3) {
        // /scripts/:category → 뒤로 가면 /scripts
        backPath = "/scripts";
      } else if (pathParts.length === 4) {
        // /scripts/:category/:problemId → 뒤로 가면 /scripts/:category
        backPath = `/scripts/${pathParts[2]}`;
      } else if (pathParts.length === 5 && pathParts[4] === "write") {
        // /scripts/:category/:problemId/write → 뒤로 가면 /scripts/:category/:problemId
        backPath = `/scripts/${pathParts[2]}/${pathParts[3]}`;
      }

      setCustomBackAction(() => () => navigate(backPath));
    } else {
      setCustomBackAction(null);
    }

    // 경로에 따라 기본 타이틀 설정
    let defaultTitle = "";

    if (location.pathname.includes("/tests/feedback")) {
      defaultTitle = "실전 연습 피드백";
    } else if (location.pathname.includes("/tests/practice")) {
      defaultTitle = "실전 연습";
    } else if (location.pathname.includes("/tests")) {
      defaultTitle = "실전 연습";
    } else if (location.pathname.includes("/scripts")) {
      defaultTitle = "나만의 스크립트 만들기";
    } else if (location.pathname.includes("/auth/survey")) {
      defaultTitle = "Background Survey";
    } else if (location.pathname.includes("/auth/profile")) {
      defaultTitle = "회원정보 입력";
    }

    setTitle(defaultTitle);
  }, [location.pathname, navigate]);

  // contextValue를 useMemo로 감싸기
  const contextValue = useMemo(
    () => ({
      title,
      setTitle,
      hideHeader,
      setHideHeader,
      hideBackButton,
      setHideBackButton,
      customBackAction,
      setCustomBackAction,
      testEndAction,
      setTestEndAction,
    }),
    [title, hideHeader, hideBackButton, customBackAction, testEndAction]
  ); // 상태 값만 의존성으로 설정
  return (
    <HeaderContext.Provider value={contextValue}>
      {children}
    </HeaderContext.Provider>
  );
};

// 커스텀 훅: 헤더 컨텍스트 사용
export const useHeader = () => {
  const context = useContext(HeaderContext);
  if (context === undefined) {
    throw new Error("useHeader must be used within a HeaderProvider");
  }
  return context;
};

// 커스텀 훅: 헤더 제목 설정
export const useHeaderTitle = (title: string) => {
  const { setTitle } = useHeader();

  useEffect(() => {
    setTitle(title);

    // 컴포넌트 언마운트 시 초기화 (옵션)
    return () => {
      setTitle("나만의 스크립트");
    };
  }, [title, setTitle]);
};

// 커스텀 훅: 뒤로가기 버튼 숨김/표시
export const useHeaderBackButton = (
  hide: boolean = false,
  customAction?: () => void
) => {
  const { setHideBackButton, setCustomBackAction } = useHeader();

  useEffect(() => {
    setHideBackButton(hide);
    if (customAction) {
      setCustomBackAction(() => customAction);
    } else {
      setCustomBackAction(null);
    }

    // 컴포넌트 언마운트 시 초기화
    return () => {
      setHideBackButton(false);
      setCustomBackAction(null);
    };
  }, [hide, customAction, setHideBackButton, setCustomBackAction]);
};

// 헤더 숨김/표시 커스텀 훅
export const useHeaderVisibility = (hide: boolean = false) => {
  const { setHideHeader } = useHeader();

  useEffect(() => {
    setHideHeader(hide);

    // 컴포넌트 언마운트 시 초기화
    return () => {
      setHideHeader(false);
    };
  }, [hide, setHideHeader]);
};

// 테스트 종료 액션 설정 훅
export const useTestEndAction = (action: () => void) => {
  const { setTestEndAction } = useHeader();

  // 특별한 식별자를 사용하여 초기 렌더링에만 실행되도록 변경
  const actionRef = React.useRef(action);

  // action이 변경될 때만 ref 업데이트
  useEffect(() => {
    actionRef.current = action;
  }, [action]);

  useEffect(() => {
    setTestEndAction(() => () => actionRef.current());

    return () => {
      setTestEndAction(null);
    };
  }, [setTestEndAction]); // action 의존성 제거
};