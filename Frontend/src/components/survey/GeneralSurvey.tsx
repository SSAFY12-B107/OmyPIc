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
          {/* 새로운 체크 SVG 사용 */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
          >
            <path
              d="M12.003 21C10.759 21 9.589 20.764 8.493 20.292C7.39767 19.8193 6.44467 19.178 5.634 18.368C4.82333 17.558 4.18167 16.606 3.709 15.512C3.23633 14.418 3 13.2483 3 12.003C3 10.7577 3.23633 9.58767 3.709 8.493C4.18167 7.39767 4.823 6.44467 5.633 5.634C6.443 4.82333 7.39533 4.18167 8.49 3.709C9.58467 3.23633 10.7547 3 12 3C13.0233 3 13.9917 3.15833 14.905 3.475C15.8183 3.79167 16.6513 4.23333 17.404 4.8L16.684 5.544C16.0253 5.05467 15.3007 4.67467 14.51 4.404C13.7193 4.13467 12.8827 4 12 4C9.78333 4 7.89567 4.77933 6.337 6.338C4.77833 7.89667 3.99933 9.784 4 12C4.00067 14.216 4.78 16.1037 6.338 17.663C7.896 19.2223 9.78333 20.0013 12 20C14.2167 19.9987 16.1043 19.2197 17.663 17.663C19.2217 16.1063 20.0007 14.2187 20 12C20 11.5973 19.9703 11.2027 19.911 10.816C19.8523 10.4287 19.764 10.052 19.646 9.686L20.444 8.869C20.6273 9.36433 20.766 9.87233 20.86 10.393C20.9533 10.913 21 11.4487 21 12C21 13.2453 20.764 14.4153 20.292 15.51C19.82 16.6047 19.1787 17.5573 18.368 18.368C17.5573 19.1787 16.6053 19.8197 15.512 20.291C14.4187 20.7623 13.249 20.9987 12.003 21ZM10.562 15.908L7.004 12.35L7.712 11.642L10.562 14.492L20.292 4.756L21 5.463L10.562 15.908Z"
              fill="#8E8E8E"
            />
          </svg>
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