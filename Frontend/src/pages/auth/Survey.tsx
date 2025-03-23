import { useState, useEffect} from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "@/hooks/useUser";
import styles from "./Survey.module.css";
import Tip from "@/components/survey/Tip";
import GeneralSurvey from '@/components/survey/GeneralSurvey';
import NavigationButton from '@/components/common/NavigationButton';
import Switch from '@/components/survey/Switch';
import MultiChoice from '@/components/survey/MultiChoice';
import surveyData from '@/data/surveyData.json';

const Survey = () => {
    const navigate = useNavigate();
    const [currentStep, setCurrentStep] = useState(0);
    const [selectedAnswers, setSelectedAnswers] = useState<Record<string, any>>({});
    const { submitSurvey } = useUser();
    
    // JSON 데이터에서 페이지 정보 가져오기
    const pages = surveyData.surveyData.pages;
    const totalPages = surveyData.surveyData.totalPages;
    
    // 중간에 있는 "안내 페이지"를 포함한 전체 단계 구성
    const steps = [
        // 0번째 단계 (첫 번째 전환 페이지)
        {
          type: "switching",
          pageId: 0
        },
        // 1~3 단계 (단일 선택 설문 페이지)
        ...pages.slice(0, 3).map(page => ({
          type: "survey",
          pageId: page.pageId,
          title: page.title,
          tip: page.tip,
          questions: page.questions
        })),
        // 4번째 단계 (다중 선택 전 안내 페이지)
        {
          type: "switching",
          pageId: 4
        },
        // 5~7 단계 (다중 선택 설문 페이지)
        ...pages.slice(3).map(page => ({
          type: page.type === "single" ? "survey" : "multichoice",
          pageId: page.pageId,
          tip: page.tip,
          questions: page.questions
        }))
    ];
      
    // 디버깅을 위해 steps 배열 출력
    console.log("Steps configuration:", steps);
    
    useEffect(() => {
        console.log("현재 단계:", currentStep);
        console.log("현재 선택된 답변:", selectedAnswers);
    }, [currentStep, selectedAnswers]);
    
    // 특정 페이지 전에 전환 페이지가 필요한지 확인
    const needsSwitchingPage = (pageId: number) => {
        // 페이지 4(여가 활동)는 다중 선택이 시작되는 시점이므로 전환 페이지가 필요
        return pageId === 4;
    };
    
    const handlePrev = () => {
        if (currentStep > 0) {
            // 현재 일반 페이지이고 이전이 전환 페이지인 경우 2단계 이전으로
            if (currentStep > 1 && steps[currentStep - 1].type === "switching") {
                setCurrentStep(prev => prev - 2);
            } else {
                setCurrentStep(prev => prev - 1);
            }
        } else {
            navigate(-1);
        }
        console.log("이전 버튼 클릭, 현재 단계:", currentStep);
    };

    const handleNext = () => {
        console.log("다음 버튼 클릭됨, 현재 단계:", currentStep);
        
        // 현재 단계가 마지막 단계가 아닌 경우
        if (currentStep < steps.length - 1) {
          // 현재 단계가 3번째 설문(단일 선택)이고, 다음이 다중 선택의 시작인지 확인
          if (currentStepData.type === "survey" && currentStepData.pageId === 3) {
            // 다중 선택 전 전환 페이지로 이동 (인덱스는 설정에 따라 다를 수 있음)
            const switchingPageIndex = steps.findIndex(step => 
              step.type === "switching" && step.pageId === 4
            );
            
            if (switchingPageIndex !== -1) {
              setCurrentStep(switchingPageIndex);
              console.log("다중 선택 전 전환 페이지로 이동");
            } else {
              // 전환 페이지가 없으면 다음 단계로
              setCurrentStep(prev => prev + 1);
            }
          } else {
            // 일반적인 다음 단계 이동
            setCurrentStep(prev => prev + 1);
          }
        } else {
          // 실제로 마지막 단계라면 제출 처리 또는 다른 곳으로 이동
          console.log("설문 모두 완료, 제출 처리");
    
          handleSubmit();
          navigate("/");
        }
    };

    // 현재 단계 데이터
    const currentStepData = steps[currentStep];
    
    // 답변 업데이트 핸들러
    const updateAnswer = (questionId: string, value: any) => {
        setSelectedAnswers(prev => ({
            ...prev,
            [questionId]: value
        }));
    };

    // 단일 선택 답변 설정
    const handleSingleSelect = (questionId: string, value: any) => {
        updateAnswer(questionId, value);
    };

    // 다중 선택 답변 설정
    const handleMultiSelect = (questionId: string, values: any[]) => {
        updateAnswer(questionId, values);
    };

    // 현재 선택된 답변 가져오기
    const getSelectedValue = (questionId: string) => {
        return selectedAnswers[questionId] || null;
    };

    // 다중 선택 항목의 총 선택 개수 계산
    const getTotalSelectedItems = () => {
    let total = 0;
    
    // 모든 다중 선택 문항(4-7번)의 ID 목록
    const multiChoiceQuestionIds = pages
      .filter(page => page.type === 'multiple')
      .flatMap(page => page.questions.map(q => q.id));
    
    // 각 문항에 대해 선택된 항목 개수 합산
    multiChoiceQuestionIds.forEach(questionId => {
      const selected = selectedAnswers[questionId];
      if (selected && Array.isArray(selected)) {
        total += selected.length;
      }
    });
    
    return total;
    };

    // 설문 데이터 제출 함수
    const handleSubmit = async () => {
        try {
        // 서베이 데이터 구성
        const surveyData = {
            profession: selectedAnswers['profession'],
            is_student: selectedAnswers['is_student'] === true || selectedAnswers['is_student'] === 'true',
            studied_lecture: selectedAnswers['studied_lecture'],
            living_place: selectedAnswers['living_place'],
            info: [] // 다중 선택 항목 통합
        };
        
        // 모든 다중 선택 응답 통합
        const multiChoiceQuestionIds = pages
            .filter(page => page.type === 'multiple')
            .flatMap(page => page.questions.map(q => q.id));
        
        multiChoiceQuestionIds.forEach(questionId => {
            const selected = selectedAnswers[questionId];
            if (selected && Array.isArray(selected)) {
            surveyData.info = [...surveyData.info, ...selected];
            }
        });
        
        console.log('제출할 서베이 데이터:', surveyData);
        
        // 서베이 제출
        const result = await submitSurvey(surveyData);
        
        if (result.success) {
            // 제출 성공 시 메인 페이지로 이동
            navigate('/');
        }
        // 실패 시 오류 처리는 이미 useUser 훅에서 처리됨
        } catch (error) {
        console.error('서베이 제출 오류:', error);
        }
    };

    return (
        <div className={styles.surveyContainer}>
            {currentStepData.type === "switching" ? (
                // 전환 페이지 (0번째 또는 다중 선택 전 안내 페이지)
                <Switch 
                    onPrev={handlePrev} 
                    onNext={handleNext}
                    step={currentStep}
                    pageId={currentStepData.pageId}
                />
            ) : currentStepData.type === "survey" ? (
                // 단일 선택 설문
                <>  
                    <div className={styles.choice}>
                        {currentStepData.questions.map((question, index) => (
                            <div key={question.id} className={index > 0 ? styles.additionalQuestion : ''}>
                                <GeneralSurvey 
                                    questionNumber={`${currentStepData.pageId}`}
                                    questionText={question.question}
                                    choices={question.options.map(opt => ({
                                        id: opt.value,
                                        text: opt.label,
                                        recommended: opt.recommended || false
                                    }))}
                                    selected={getSelectedValue(question.id)}
                                    onSelect={(value) => handleSingleSelect(question.id, value)}
                                />
                            </div>
                        ))}
                    </div>

                    <div className={styles.content}>
                        <Tip tipNumber={currentStepData.pageId} />
                    </div>
                    
                    <div className={styles["button-group"]}>
                        <NavigationButton 
                            type="prev" 
                            onClick={handlePrev}
                        />
                        <NavigationButton 
                            type="next" 
                            onClick={handleNext}
                        />
                    </div>
                </>
            ) : (
                // 다중 선택 설문
                <>
                <div className={styles.surveyTitle}>
                    <h2>{currentStepData.title}</h2>
                    {currentStepData.description && (
                        <p className={styles.description}>{currentStepData.description}</p>
                    )}
                </div>
                
                {currentStepData.questions.map(question => (
                    <MultiChoice 
                        key={question.id}
                        questionNumber={`${currentStepData.pageId}`}
                        questionText={question.question}
                        choices={question.options.map(opt => ({
                            id: typeof opt.value === 'string' ? opt.value : opt.value,
                            text: opt.label,
                            recommended: opt.recommended || false
                        }))}
                        minSelect={question.minSelect || 1}
                        selected={getSelectedValue(question.id) || []}
                        onSelect={(values) => handleMultiSelect(question.id, values)}
                        totalSelected={getTotalSelectedItems()} // 추가: 총 선택 개수 전달
                        requiredTotal={12} // 필요한 총 선택 개수
                    />
                ))}
                
                <div className={styles.content}>
                    <Tip tipNumber={currentStepData.pageId} />
                </div>
                

                <div className={styles["button-group"]}>
                <NavigationButton 
                    type="prev" 
                    onClick={handlePrev}
                />
                <NavigationButton 
                    type="next" 
                    onClick={handleNext}
                    // 마지막 단계인 경우 "제출"로 텍스트 변경
                    label={currentStep === steps.length - 1 ? "제출" : "다음"}
                />
                </div>
            </>
                        )}
                    </div>
                );
            };

export default Survey;