import React, { useState } from "react";
import styles from "./GeneralSurvey.module.css";

type ChoiceItem = {
  id: number;
  text: string;
  recommended: boolean;
};

type GeneralSurveyProps = {
  questionNumber: string | number;
  questionText: string;
  choices?: ChoiceItem[];
};

const GeneralSurvey = ({ questionNumber, questionText, choices }: GeneralSurveyProps) => {
  // 선택된 항목 상태 관리
  const [selectedItem, setSelectedItem] = useState<number | null>(null);

  // 선택 항목 데이터 - props로 받거나 기본값 사용
  const choiceItems = choices || [

  ];

  // 항목 클릭 핸들러
  const handleItemClick = (itemId: number) => {
    setSelectedItem(itemId === selectedItem ? null : itemId);
  };

  return (
    <div className={styles.box}>
      <div className={styles.group2}>
        {/* 질문 헤더 */}
        <div className={styles.questionHeader}>
          <div className={styles.questionCheck}>✓</div>
          <div className={styles.questionText}>
            {questionNumber}. {questionText}
          </div>
        </div>

        {/* 선택 항목들 */}
        {choiceItems.map((item) => (
          <div 
            key={item.id} 
            className={`${styles.frame} ${selectedItem === item.id ? styles.selected : ""}`} 
            onClick={() => handleItemClick(item.id)}
          >
            <div className={styles.textWrapper2}>{item.text}</div>
            {item.recommended && (
              <span className={styles.star}>★</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default GeneralSurvey;