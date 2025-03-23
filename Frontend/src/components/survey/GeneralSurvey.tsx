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
};

function GeneralSurvey({ 
  questionNumber, 
  questionText, 
  choices,
  selected = null,
  onSelect 
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
    <div className={styles.box}>
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
            className={`${styles.frame} ${selectedChoice === choice.id ? styles.selected : ''}`}
            onClick={() => handleSelectChoice(choice.id)}
          >
            {choice.recommended && (
              <span className={styles.star}>★</span>
            )}
            <span className={styles.textWrapper2}>{choice.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default GeneralSurvey;