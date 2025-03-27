import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { useCallback, useState } from "react";
import styles from "./ScriptModal.module.css";
import opigi from "@/assets/images/opigi.png";
import LoadingSpinner from "@/components/common/LoadingSpinner"; // 기존 로딩 스피너 import
import { setContent, setQuestions, setIsCustomMode } from "@/store/scriptSlice";
import { QuestionsResponse, useGenerateCustomQuestions } from "@/hooks/useScripts";

interface Props {
  isGenerating: boolean;
  onClose: () => void;
  scriptContent: string;
  detailPagePath: string;
  problemId: string;
  currentAnswers: string[];
}

function ScriptModal({
  isGenerating,
  onClose,
  scriptContent = "",
  detailPagePath,
  problemId,
  currentAnswers,
}: Props) {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const generateCustomQuestionsMutation = useGenerateCustomQuestions();
  
  // 꼬리 질문 생성 중 상태 추가
  const [isGeneratingCustom, setIsGeneratingCustom] = useState(false);

  // AI 꼬리 질문 생성 함수
  const generateCustomQuestions = useCallback(() => {
    if (!problemId) return;

    // 꼬리 질문 생성 중 상태로 변경
    setIsGeneratingCustom(true);

    // 기본 질문에 대한 답변을 꼬리 질문 생성 요청으로 변환
    const customQuestionsRequest = {
      question1: currentAnswers[0] || '',
      question2: currentAnswers[1] || '',
      question3: currentAnswers[2] || ''
    };

    generateCustomQuestionsMutation.mutate(
      { problemId, answers: customQuestionsRequest },
      {
        onSuccess: (data: QuestionsResponse) => {
          setIsGeneratingCustom(false);
          if (data.content) {
            dispatch(setContent(data.content));
          }
          if (data.questions) {
            dispatch(setQuestions(data.questions));
          }
          dispatch(setIsCustomMode(true));
          onClose(); // 모달 닫기
        },
        onError: (error: Error) => {
          setIsGeneratingCustom(false);
          console.error("AI 꼬리 질문 생성 중 오류가 발생했습니다.", error);
          navigate(detailPagePath);
        },
      }
    );
  }, [problemId, currentAnswers, detailPagePath, navigate, dispatch, generateCustomQuestionsMutation, onClose]);

  // 네 버튼 클릭 핸들러
  const handleYesClick = () => {
    generateCustomQuestions();
  };

  // 아니요 버튼 클릭 핸들러
  const handleNoClick = () => {
    onClose();
    navigate(detailPagePath);
  };

  return (
    <div className={styles.overlay}>
      <div className={styles.scriptModal}>
        <div className={styles.modalTitle}>
          {isGenerating
            ? "스크립트를 생성하고 있어요"
            : isGeneratingCustom 
              ? "AI 꼬리 질문을 생성하고 있어요" 
              : "스크립트가 완성되었어요!"}
        </div>
        
        {/* 로딩 중이거나 완료된 상태에 따라 다른 UI 표시 */}
        {isGeneratingCustom ? (
          <div className={styles.loadingWrapper}>
            <LoadingSpinner />
          </div>
        ) : (
          <img 
            src={opigi} 
            alt="opigi-img" 
            className={isGenerating ? styles.generatingImage : styles.completedImage} 
          />
        )}

        {isGenerating ? (
          // 스크립트 생성 중일 경우
          <div className={styles.tipBox}>
            <div className={styles.tipTitleBox}>
              <span>Tip</span>
              <p>최대한 많이 말하기</p>
            </div>
            <div className={styles.tipTxt}>
              2분 꽉 채워 말하면 고득점 확률 UP!<br/>생각나는 관련 내용을 덧붙여보세요
            </div>
          </div>
        ) : isGeneratingCustom ? (
          // 꼬리 질문 생성 중일 경우
          <div className={styles.tipBox}>
            <div className={styles.tipTitleBox}>
              <span>Tip</span>
              <p>AI가 더 구체적인 질문을 생성 중입니다</p>
            </div>
            <div className={styles.tipTxt}>
              잠시만 기다려주세요. 귀하의 답변을 바탕으로<br/>
              더 깊이 있는 질문을 준비하고 있습니다.
            </div>
          </div>
        ) : (
          // 스크립트 생성 완료된 경우
          <>
            <div className={styles.scriptBox}>
              <p dangerouslySetInnerHTML={{ __html: scriptContent }} />
            </div>

            <div className={styles.additionalQ}>
              <p>
                AI와 추가로 대화해
                <br />더 구체적인 답변을 받아보시겠어요?
              </p>
              <div className={styles.btnBox}>
                <button 
                  className={styles.yesBtn} 
                  onClick={handleYesClick}
                  disabled={isGeneratingCustom}
                >
                  네
                </button>
                <button 
                  className={styles.noBtn} 
                  onClick={handleNoClick}
                  disabled={isGeneratingCustom}
                >
                  아니요
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default ScriptModal;