import { useNavigate } from 'react-router-dom';
import styles from "./ScriptModal.module.css";
import opigi from "../../assets/images/opigi.png";

interface Props {
  isGenerating: boolean; // 스크립트 생성 중인지 여부
  onClose?: () => void;
  scriptContent?: string; // 생성된 스크립트 내용
}

function ScriptModal({ isGenerating, onClose, scriptContent = '' }: Props) {
  const navigate = useNavigate();

  return (
    <div className={styles.overlay}>
      <div className={styles.scriptModal}>
        <div className={styles.modalTitle}>
          {isGenerating
            ? "스크립트를 생성하고 있어요"
            : "스크립트가 완성되었어요!"}
        </div>
        <img src={opigi} alt="opigi-img" className={isGenerating ? styles.generatingImage : styles.completedImage} />

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
        ) : (
          // 스크립트 생성 완료된 경우
          <>
            <div className={styles.scriptBox}>
              <p>
                {scriptContent}
              </p>
            </div>

            <div className={styles.additionalQ}>
              <p>
                AI와 추가로 대화해
                <br />더 구체적인 답변을 받아보시겠어요?
              </p>
              <div className={styles.btnBox}>
              <button 
                  className={styles.yesBtn} 
                  onClick={() => {
                    if (onClose) onClose();
                  }}
                >
                  네
                </button>
                <button 
                  className={styles.noBtn} 
                  onClick={() => {
                    if (onClose) onClose();
                    navigate('/script/detail');
                  }}
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
