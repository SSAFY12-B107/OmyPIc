import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import QuestionBox from "@/components/script/QuestionBox";
import styles from "./ScriptWrite.module.css";
import opigi from "@/assets/images/opigi.png";
import ScriptModal from "@/components/script/ScriptModal";
import NavigationButton from "@/components/common/NavigationButton";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import {
  CreateScriptResponse,
  useGetBasicQuestions,
  useCreateScript
} from "@/hooks/useScripts";
import { 
  setContent, 
  setQuestions,
  setCurrentStep, 
  nextStep, 
  prevStep, 
  setCurrentAnswer, 
  clearScriptState,
  getCurrentAnswers,
  getScriptRequestData,
  TOTAL_STEPS
} from "@/store/scriptSlice";

// Redux 상태 타입 정의
interface RootState {
  script: {
    content: string;
    questions: string[];
    currentStep: number;
    basicAnswers: string[];
    customAnswers: string[];
    isCustomMode: boolean;
  }
}

function ScriptWrite() {
  const { category, problemId } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  
  // Redux 상태 구독
  const content = useSelector((state: RootState) => state.script.content);
  const questions = useSelector((state: RootState) => state.script.questions);
  const currentStep = useSelector((state: RootState) => state.script.currentStep);
  const isCustomMode = useSelector((state: RootState) => state.script.isCustomMode);
  const currentAnswers = useSelector(getCurrentAnswers) as string[];
  const scriptRequestData = useSelector(getScriptRequestData);
  
  // 로컬 상태
  const [showModal, setShowModal] = useState(false);
  const [scriptContent, setScriptContent] = useState<string>("");

  // 상세 페이지 경로
  const detailPagePath = `/scripts/${category}/${problemId}`;

  // API 훅 사용
  const { data: basicQuestionsData, isLoading: isQuestionsLoading } =
    useGetBasicQuestions(problemId || '');

  const createScriptMutation = useCreateScript();

  // 기본 질문 데이터 로딩 시 Redux 상태 업데이트
  useEffect(() => {
    if (basicQuestionsData) {
      if (basicQuestionsData.content) {
        dispatch(setContent(basicQuestionsData.content));
      }
      if (basicQuestionsData.questions && basicQuestionsData.questions.length > 0) {
        dispatch(setQuestions(basicQuestionsData.questions));
      }
    }
  }, [basicQuestionsData, dispatch]);

  // 사용자 답변 저장 함수
  const handleAnswerChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      dispatch(setCurrentAnswer({ 
        index: currentStep - 1, 
        value: e.target.value 
      }));
    },
    [dispatch, currentStep]
  );

  // 이전 단계로 이동
  const handlePrev = useCallback((): void => {
    dispatch(prevStep());
  }, [dispatch]);

  // 다음 단계로 이동
  const handleNext = useCallback((): void => {
    // 현재 단계의 답변이 비어있는지 확인
    if (!currentAnswers[currentStep - 1]?.trim()) {
      alert("답변을 입력해주세요.");
      return;
    }

    if (currentStep < TOTAL_STEPS) {
      // 다음 단계로 이동
      dispatch(nextStep());
    } else {
      // 마지막 단계에서는 스크립트 생성 API 요청
      generateScript();
      dispatch(setCurrentStep(1));
    }
  }, [currentStep, currentAnswers, dispatch]);

  // 모달 닫기 함수
  const handleCloseModal = useCallback(() => {
    setShowModal(false);
  }, []);

  // 스크립트 생성 API 요청 함수
  const generateScript = useCallback(() => {
    if (!problemId) return;
    
    // 이미 커스텀 질문 모드라면 스크립트 생성 후 페이지 이동 (모달 없이)
    if (isCustomMode) {
      createScriptMutation.mutate(
        { problemId, scriptData: scriptRequestData },
        {
          onSuccess: () => {
            // 스크립트 생성 후 스크립트 상세 페이지로 바로 이동
            navigate(detailPagePath);
            dispatch(clearScriptState());
          },
          onError: (error: Error) => {
            console.error("스크립트 생성 중 오류가 발생했습니다.", error);
          }
        }
      );
      return;
    }

    // 기본 질문 모드라면 모달 표시
    setShowModal(true);
    createScriptMutation.mutate(
      { problemId, scriptData: scriptRequestData },
      {
        onSuccess: (data: CreateScriptResponse) => {
          if (data.content) {
            setScriptContent(data.content);
          }
        },
        onError: (error: Error) => {
          console.error("스크립트 생성 중 오류가 발생했습니다.", error);
          setShowModal(false);
        }
      }
    );
  }, [isCustomMode, problemId, navigate, detailPagePath, createScriptMutation, scriptRequestData, dispatch]);

  // 로딩 스피너 표시 조건
  if (isQuestionsLoading && questions.length === 0) {
    return <LoadingSpinner />;
  }

  return (
    <div className={styles.scriptWriteContainer}>
      {/* 질문 */}
      {content && (
        <QuestionBox title="질문" content={content} />
      )}

      {/* 프로그래스 바 */}
      <div className={styles.progressBox}>
        {Array.from({ length: TOTAL_STEPS }, (_, idx) => (
          <div
            key={idx}
            className={`${styles.progressBar} ${
              idx < currentStep ? styles.active : ""
            }`}
          ></div>
        ))}
      </div>

      {/* ai 채팅 */}
      <div className={styles.chatBox}>
        {questions.length > 0 && currentStep <= questions.length && (
          <>
            <div className={`${styles.opigiBox} ${styles.chatTxtBox}`}>
              <div className={styles.imgBox}>
                <img src={opigi} alt="opigi-img" />
                <p>오피기</p>
              </div>
              <div className={styles.chat}>{questions[currentStep - 1]}</div>
            </div>
            <div className={`${styles.myBox} ${styles.chatTxtBox}`}>
              <textarea
                className={styles.chat}
                placeholder="답변 입력하기"
                value={currentAnswers[currentStep - 1] || ''}
                onChange={handleAnswerChange}
              ></textarea>
              <div className={styles.imgBox}>
                <img src={opigi} alt="" />
                <p>나</p>
              </div>
            </div>
          </>
        )}
      </div>

      {/* 이전/다음 버튼 */}
      <div className={styles.navigationContainer}>
        <NavigationButton 
          type="prev" 
          onClick={handlePrev} 
        />
        <NavigationButton 
          type="next" 
          onClick={handleNext} 
        />
      </div>

      {/* 모달 */}
      {showModal && (
        <ScriptModal
          isGenerating={createScriptMutation.isPending}
          onClose={handleCloseModal}
          scriptContent={scriptContent}
          detailPagePath={detailPagePath}
          problemId={problemId || ''}
          currentAnswers={currentAnswers}
        />
      )}
    </div>
  );
}

export default ScriptWrite;