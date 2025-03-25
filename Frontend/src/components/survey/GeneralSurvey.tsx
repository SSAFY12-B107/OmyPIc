import { useState, useEffect } from 'react';
import styles from './GeneralSurvey.module.css';

type Choice = {
  id: number | string;
  text: string;
  recommended?: boolean;
};

type Props = {
  questionNumber: string;
  questionText: string;
  choices: Choice[];
  selected?: number | string | null;
  onSelect?: (value: number | string) => void;
  hasError?: boolean;
};

function GeneralSurvey({ 
  questionNumber, 
  questionText, 
  choices,
  selected = null,
  onSelect,
  hasError = false
}: Props) {
  const [selectedChoice, setSelectedChoice] = useState<number | string | null>(selected);

  // 부모로부터 받은 선택 값이 변경되면 상태 업데이트
  useEffect(() => {
    setSelectedChoice(selected);
  }, [selected]);

  const handleSelectChoice = (id: number | string) => {
    setSelectedChoice(id);
    
    // 부모 컴포넌트에 선택 사항 알리기
    if (onSelect) {
      onSelect(id);
    }
  };

  return (
    <div className={`${styles.box} ${hasError ? styles.errorBorder : ''}`}>
      {/* 질문 헤더 */}
      <div className={styles.questionHeader}>
        <div className={styles.questionCheck}>
          <span>✓</span>
        </div>
        <h3 className={styles.questionText}>{questionNumber}. {questionText}</h3>
      </div>
      
      {/* 선택지 목록 */}
      <div className={styles.group2}>
        {choices.map((choice) => (
          <div
            key={choice.id}
            className={`${styles.frame} ${selectedChoice === choice.id ? styles.selected : ''} ${choice.recommended ? styles.hasStarIcon : ''}`}
            onClick={() => handleSelectChoice(choice.id)}
          >
            {choice.recommended && (
              <div className={styles.starIcon}>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                  <path
                    d="M50,10 C52,10 53.5,11 54.5,13 L65,33 C65.5,34 66.5,35 68,35.2 L90,38 C92,38.5 93.5,40 94,42 C94.5,44 93.5,46 92,47.5 L76,63 C75,64 74.5,65.5 75,67 L79,89 C79.5,91 78.5,93 77,94.5 C75.5,95.5 73.5,96 71.5,95 L52,85 C50.5,84.5 49,84.5 47.5,85 L28,95 C26,96 24,95.5 22.5,94.5 C21,93 20,91 20.5,89 L24.5,67 C25,65.5 24.5,64 23.5,63 L8,47.5 C6.5,46 5.5,44 6,42 C6.5,40 8,38.5 10,38 L32,35.2 C33.5,35 34.5,34 35,33 L45.5,13 C46.5,11 48,10 50,10 Z"
                    fill="#C09EFF"
                    stroke="none"
                  />
                </svg>
              </div>
            )}
            <span className={styles.textWrapper2}>{choice.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default GeneralSurvey;