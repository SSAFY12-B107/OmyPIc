import { useState, useEffect } from "react";
import styles from "./MultiChoice.module.css";

type ChoiceItem = {
  id: string | number;
  text: string;
  recommended: boolean;
};

type Props = {
  questionNumber: string;
  questionText: string;
  choices: ChoiceItem[];
  minSelect?: number;
  selected?: (string | number)[];
  onSelect?: (selected: (string | number)[]) => void;
  totalSelected?: number; // 추가: 전체 문항에 대한 총 선택 개수
  requiredTotal?: number; // 추가: 요구되는 총 선택 개수
};

function MultiChoice({ 
  questionNumber, 
  questionText, 
  choices, 
  minSelect = 1,
  selected = [],
  onSelect,
  totalSelected = 0, // 기본값 설정
  requiredTotal = 12 // 기본값 설정
}: Props) {
  // 선택된 항목들을 관리하는 상태
  const [selectedItems, setSelectedItems] = useState<(string | number)[]>(selected);

  // 부모로부터 받은 선택 항목이 변경되면 상태 업데이트
  useEffect(() => {
    setSelectedItems(selected);
  }, [selected]);

  // 항목 클릭 핸들러
  const handleItemClick = (itemId: string | number) => {
    const updatedItems = selectedItems.includes(itemId)
      ? selectedItems.filter(id => id !== itemId)
      : [...selectedItems, itemId];
    
    setSelectedItems(updatedItems);
    
    // 부모 컴포넌트에 변경 사항 알리기
    if (onSelect) {
      onSelect(updatedItems);
    }
  };

  // Survey 컴포넌트 내 handleMultiSelect
  const handleMultiSelect = (questionId: string, values: any[]) => {
    console.log(`Question ${questionId} selected values:`, values);
    updateAnswer(questionId, values);
    // 디버깅용 로그 추가
    console.log("총 선택 항목 수:", getTotalSelectedItems());
  };

  return (
    <div className={styles.multiChoiceContainer}>
      {/* 선택된 개수 정보 */}
      <div className={styles.selectInfo}>
        <p>최소 {minSelect}개</p>
        <p className={styles.curSelectInfo}>
          {totalSelected}개 항목 선택
        </p>
      </div>

      <div className={styles.multiChoiceBox}>
        {/* 질문 */}
        <div className={styles.multiChoiceQ}>
          <div>{/* 아이콘 */}</div>
          <p>{questionNumber}. {questionText}</p>
        </div>

        {/* 다중선택 항목 */}
        <div className={styles.choiceList}>
          {choices.map((item) => (
            <div
              key={item.id}
              className={`${styles.choiceItem} ${
                selectedItems.includes(item.id) ? styles.choiceItemSelected : ""
              }`}
              onClick={() => handleItemClick(item.id)}
            >
              {item.recommended && (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                  <path
                    d="M50,10 C52,10 53.5,11 54.5,13 L65,33 C65.5,34 66.5,35 68,35.2 L90,38 C92,38.5 93.5,40 94,42 C94.5,44 93.5,46 92,47.5 L76,63 C75,64 74.5,65.5 75,67 L79,89 C79.5,91 78.5,93 77,94.5 C75.5,95.5 73.5,96 71.5,95 L52,85 C50.5,84.5 49,84.5 47.5,85 L28,95 C26,96 24,95.5 22.5,94.5 C21,93 20,91 20.5,89 L24.5,67 C25,65.5 24.5,64 23.5,63 L8,47.5 C6.5,46 5.5,44 6,42 C6.5,40 8,38.5 10,38 L32,35.2 C33.5,35 34.5,34 35,33 L45.5,13 C46.5,11 48,10 50,10 Z"
                    fill="#C09EFF"
                    stroke="none"
                  />
                </svg>
              )}
              <p>{item.text}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default MultiChoice;