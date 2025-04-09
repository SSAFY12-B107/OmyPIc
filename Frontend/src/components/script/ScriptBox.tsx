import { useState, useEffect, useRef } from "react";
import styles from "./ScriptBox.module.css";
import { usePronunciationAudio } from "@/hooks/usePronunciation";

interface ScriptBoxProps {
  userScript: Array<{
    _id: string;
    content: string;
  }>;
}

function ScriptBox({ userScript }: ScriptBoxProps) {
  // 오디오 관련 상태
  const [activeScriptId, setActiveScriptId] = useState<string | null>(null);

  // 발음 듣기 API 훅 사용 - 필요할 때만 활성화
  const {
    data: audioData,
    isLoading,
  } = usePronunciationAudio(activeScriptId);

  // 첫 번째 스크립트 데이터 미리 가져오기
  useEffect(() => {
    if (userScript.length > 0) {
      // 첫 번째 스크립트의 ID로 상태를 설정하여 데이터를 미리 로드
      setActiveScriptId(userScript[0]._id);
    }
  }, [userScript]); // userScript가 변경될 때마다 실행

  // 발음 듣기 요청 핸들러
  const handleRequestAudio = (scriptId: string) => {
    setActiveScriptId(scriptId);
  };

  return (
    <div className={styles["script-box"]}>
      {/* header */}
      <div className={styles["script-box-header"]}>
        <div className={styles["title-box"]}>
          <div className={styles["icon-box"]}>
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
          <p>나만의 스크립트</p>
        </div>
      </div>

      {/* content */}
      <div className={styles.contentList}>
        {userScript.length > 0 ? (
          // 스크립트 생성된 경우
          userScript.map((script) => (
            <div key={`script-${script._id}`} className={styles["content-item"]}>
              <p dangerouslySetInnerHTML={{ __html: script.content }} />
              
              {/* 오디오 데이터가 있으면 오디오 플레이어만 표시, 없으면 발음 듣기 버튼 표시 */}
              {audioData?.audio_base64 && activeScriptId === script._id ? (
                <audio
                  controls
                  className={styles["audio-player"]}
                  src={`data:audio/${audioData.audio_type || "mp3"};base64,${audioData.audio_base64}`}
                />
              ) : (
                isLoading && activeScriptId === script._id ? (
                  <button className={styles["listen-btn"]}>
                    <div className={styles.spinner}></div>
                    <span>로딩 중...</span>
                  </button>
                ) : (
                  <button 
                    className={styles["listen-btn"]} 
                    onClick={() => handleRequestAudio(script._id)}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="20"
                      height="20"
                      viewBox="0 0 20 20"
                      fill="none"
                    >
                      <path
                        d="M8.65417 12.6917L12.6917 10L8.65333 7.30833L8.65417 12.6917ZM10 17.5C8.96444 17.5 7.99056 17.3053 7.07833 16.9158C6.16611 16.5264 5.3725 15.9942 4.6975 15.3192C4.0225 14.6442 3.4875 13.8528 3.0925 12.945C2.6975 12.0383 2.5 11.0678 2.5 10.0333C2.5 9.53222 2.54639 9.03889 2.63917 8.55333C2.73194 8.06778 2.87 7.59139 3.05333 7.12417L3.70333 7.77417C3.58167 8.13528 3.48972 8.50111 3.4275 8.87167C3.36528 9.24222 3.33389 9.61833 3.33333 10C3.33333 11.8611 3.97917 13.4375 5.27083 14.7292C6.5625 16.0208 8.13889 16.6667 10 16.6667C11.8611 16.6667 13.4375 16.0208 14.7292 14.7292C16.0208 13.4375 16.6667 11.8611 16.6667 10C16.6667 8.13889 16.0208 6.5625 14.7292 5.27083C13.4375 3.97917 11.8611 3.33333 10 3.33333C9.625 3.33333 9.255 3.36444 8.89 3.42667C8.525 3.48889 8.16389 3.58111 7.80667 3.70333L7.16 3.0575C7.59833 2.8825 8.04444 2.74583 8.49833 2.6475C8.95222 2.54917 9.42083 2.5 9.90417 2.5C10.9497 2.5 11.9342 2.69472 12.8575 3.08417C13.7808 3.47361 14.5853 4.00861 15.2708 4.68917C15.9564 5.36972 16.4994 6.16611 16.9 7.07833C17.3006 7.99056 17.5006 8.96444 17.5 10C17.4994 11.0356 17.3022 12.0094 16.9083 12.9217C16.5133 13.8339 15.9783 14.6275 15.3033 15.3025C14.6278 15.9781 13.8339 16.5131 12.9217 16.9075C12.0094 17.3025 11.0356 17.5 10 17.5ZM4.93583 5.67333C4.73806 5.67333 4.56583 5.59972 4.41917 5.4525C4.2725 5.30583 4.19917 5.13361 4.19917 4.93583C4.19917 4.73806 4.2725 4.56583 4.41917 4.41917C4.56583 4.2725 4.73806 4.19917 4.93583 4.19917C5.13361 4.19917 5.30583 4.2725 5.4525 4.41917C5.59917 4.56583 5.67278 4.73806 5.67333 4.93583C5.67389 5.13361 5.60028 5.30583 5.4525 5.4525C5.30472 5.59917 5.1325 5.67278 4.93583 5.67333Z"
                        fill="#5E5E5E"
                        fillOpacity="0.5"
                      />
                    </svg>
                    <span>발음 듣기</span>
                  </button>
                )
              )}
            </div>
          ))
        ) : (
          <p className={styles.noContent}>아직 생성된 스크립트가 없습니다.</p>
        )}
      </div>
    </div>
  );
}

export default ScriptBox;