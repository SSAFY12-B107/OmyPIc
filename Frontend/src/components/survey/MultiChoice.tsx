import { useState } from "react";
import styles from "./MultiChoice.module.css";

type Props = {};

function MultiChoice({}: Props) {
  // 선택된 항목들을 관리하는 상태
  const [selectedItems, setSelectedItems] = useState<number[]>([]);

  // 예시 데이터
  const choiceItems = [
    { id: 1, text: "영화 보기", recommended: true },
    { id: 2, text: "공연 보기", recommended: true },
    { id: 3, text: "자원 봉사", recommended: false },
  ];

  // 항목 클릭 핸들러
  const handleItemClick = (itemId: number) => {
    setSelectedItems((prev) => {
      // 이미 선택되어 있으면 제거
      if (prev.includes(itemId)) {
        return prev.filter((id) => id !== itemId);
      }
      // 아니면 추가
      else {
        return [...prev, itemId];
      }
    });
  };

  return (
    <div className={styles.multiChoiceContainer}>
      {/* 선택된 개수 정보 */}
      <div className={styles.selectInfo}>
        <p>최소 12개</p>
        <p className={styles.curSelectInfo}>
          []개 항목 선택
        </p>
      </div>

      <div className={styles.multiChoiceBox}>
        {/* 질문 */}
        <div className={styles.multiChoiceQ}>
          <div>{/* 아이콘 */}</div>
          <p>[1]. [귀하는 여가 활동으로 주로 무엇을 합니까?]</p>
        </div>

        {/* 다중선택 항목 */}
        <div className={styles.choiceList}>
          {choiceItems.map((item) => (
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