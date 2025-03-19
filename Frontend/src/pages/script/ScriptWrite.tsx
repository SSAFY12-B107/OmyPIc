import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import QuestionBox from "../../components/script/QuestionBox";
import styles from "./ScriptWrite.module.css";
import opigi from "../../assets/images/opigi.png";
import ScriptModal from "../../components/script/ScriptModal";
import NavigationButton from "../../components/common/NavigationButton";
import LoadingSpinner from "../../components/common/LoadingSpinner";
import {
  useGetBasicQuestions,
  useCreateScript,
  useGenerateCustomQuestions,
} from "../../hooks/useScripts";

type Props = {
  problemId: string;
  category: string;
};

function ScriptWrite({ problemId, category }: Props) {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [showModal, setShowModal] = useState(false);
  const [questions, setQuestions] = useState<string[]>([]);
  const [answers, setAnswers] = useState<string[]>(["", "", ""]);
  const [scriptContent, setScriptContent] = useState<string>("");
  const [isCustomQuestions, setIsCustomQuestions] = useState<boolean>(false);
  const totalSteps = 3;

  // 상세 페이지 경로
  const detailPagePath = `/scripts/${category}/${problemId}`;

  // API 훅 사용
  const { data: basicQuestionsData, isLoading: isQuestionsLoading } =
    useGetBasicQuestions(problemId);

  const createScriptMutation = useCreateScript();
  const generateCustomQuestionsMutation = useGenerateCustomQuestions();

  // 기본 질문 데이터 로딩 시 상태 업데이트
  useEffect(() => {
    if (
      basicQuestionsData?.questions &&
      basicQuestionsData.questions.length > 0
    ) {
      setQuestions(basicQuestionsData.questions);
    }
  }, [basicQuestionsData]);

  // 사용자 답변 저장 함수
  const handleAnswerChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const newAnswers = [...answers];
      newAnswers[currentStep - 1] = e.target.value;
      setAnswers(newAnswers);
    },
    [answers, currentStep]
  );

  // 이전 단계로 이동
  const handlePrev = useCallback((): void => {
    if (currentStep > 1) {
      setCurrentStep((prev) => prev - 1);
    }
  }, [currentStep]);

  // 다음 단계로 이동
  const handleNext = useCallback((): void => {
    // 현재 단계의 답변이 비어있는지 확인
    if (!answers[currentStep - 1]?.trim()) {
      alert("답변을 입력해주세요.");
      return;
    }

    if (currentStep < totalSteps) {
      // 다음 단계로 이동
      setCurrentStep((prev) => prev + 1);
    } else {
      // 마지막 단계에서는 스크립트 생성 API 요청
      generateScript();
    }
  }, [currentStep, answers, totalSteps]);

  // AI 꼬리 질문 생성 함수
  const generateCustomQuestions = useCallback(() => {
    setShowModal(false);

    generateCustomQuestionsMutation.mutate(problemId, {
      onSuccess: (data) => {
        setQuestions(data.questions);
        setAnswers(["", "", ""]);
        setCurrentStep(1);
        setIsCustomQuestions(true);
      },
      onError: (error) => {
        console.error("AI 꼬리 질문 생성 중 오류가 발생했습니다.", error);
        navigate(detailPagePath);
      },
    });
  }, [problemId, detailPagePath, navigate]);

  // 모달 닫기 함수
  const handleCloseModal = useCallback(() => {
    setShowModal(false);
  }, []);

  // 스크립트 생성 API 요청 함수
const generateScript = useCallback(() => {
  // 이미 커스텀 질문 모드라면 스크립트 생성 후 페이지 이동 (모달 없이)
  if (isCustomQuestions) {
    createScriptMutation.mutate({ 
      problemId, 
      answers 
    }, {
      onSuccess: () => {
        // 스크립트 생성 후 스크립트 상세 페이지로 바로 이동
        navigate(detailPagePath);
      },
      onError: (error) => {
        console.error("스크립트 생성 중 오류가 발생했습니다.", error);
      }
    });
    return;
  }

  // 기본 질문 모드라면 모달 표시
  setShowModal(true);
  createScriptMutation.mutate({ 
    problemId, 
    answers 
  }, {
    onSuccess: (data) => {
      setScriptContent(data.script);
    },
    onError: (error) => {
      console.error("스크립트 생성 중 오류가 발생했습니다.", error);
      setShowModal(false);
    }
  });
}, [isCustomQuestions, problemId, answers, navigate, detailPagePath, createScriptMutation]);

  // 로딩 스피너 표시 조건
  if (
    (isQuestionsLoading || generateCustomQuestionsMutation.isPending) &&
    questions.length === 0
  ) {
    return <LoadingSpinner />;
  }

  return (
    <div className={styles.scriptWriteContainer}>
      {/* 공통 header */}

      {/* 질문 */}
      {questions.length > 0 && (
        <QuestionBox title="질문" content={questions[currentStep - 1]} />
      )}

      {/* 프로그래스 바 */}
      <div className={styles.progressBox}>
        {Array.from({ length: totalSteps }, (_, idx) => (
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
        {questions.length > 0 && (
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
                value={answers[currentStep - 1] || ''}
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
          onConfirm={generateCustomQuestions}
          scriptContent={scriptContent}
          detailPagePath={detailPagePath}
        />
      )}
    </div>
  );
}

export default ScriptWrite;