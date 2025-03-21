// src/pages/TestExam.tsx
import styles from "./TestExam.module.css";
import avatar from "../../assets/images/avatar.png";
import animation from "../../assets/images/speaking_animate.png";
import { useState, useRef, useEffect, useCallback } from "react";
import { RootState } from "../../store";
import { useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import MicRecorder from "mic-recorder-to-mp3-fixed";
import apiClient from "../../api/apiClient";
import { useAudio, getAudioUrl } from "../../hooks/useAudio";

function TestExam() {
  const navigate = useNavigate();
  const { currentTest } = useSelector((state: RootState) => state.tests);

  // 테스트 타입에 따른 최대 문제 수 설정
  const maxValue = currentTest?.test_type ? 15 : 7;

  // 문제번호 관리
  const [currentProblem, setCurrentProblem] = useState(1);
  // 듣기 오디오 버퍼링 관리
  const [isLoading, setIsLoading] = useState(false);

  // 오디오 상태
  const audioRef = useRef(new Audio());

  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [hasPlayed, setHasPlayed] = useState(false);
  const [hasListenedAgain, setHasListenedAgain] = useState(false);

  // 녹음 상태
  const [recorder, setRecorder] = useState<MicRecorder | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedFile, setRecordedFile] = useState<File | null>(null);

  // API 관련
  const currentProblemId = currentTest
    ? currentTest.problem_data[currentProblem].problem_id
    : "";
  const { data: audioData, isLoading: isAudioLoading } =
    useAudio(currentProblemId);
  const audioUrl = audioData ? getAudioUrl(audioData) : null;

  useEffect(() => {
    // load()를 굳이 쓰는 이유는 뭐지? 
    if (!isAudioLoading && audioUrl) {
      audioRef.current.src = audioUrl;
      audioRef.current.load();
    }
    else (!audioUrl)
    console.log('오디오주소없음',audioUrl)
    console.log('audioData',audioData)
    
  }, [isAudioLoading, audioUrl, currentProblem]);

  

  // 오디오 이벤트 설정
  useEffect(() => {
    const audio = audioRef.current;

    const handleEnded = () => {
      setIsPlaying(false);
      setIsPaused(false);
      setHasPlayed(true);
    };

    const handlePlay = () => {
      setIsPlaying(true);
      setIsPaused(false);
    };

    const handlePause = () => {
      if (!audio.ended) {
        setIsPlaying(false);
        setIsPaused(true);
      }
    };

    const handleWaiting = () => setIsLoading(true);
    const handleCanPlay = () => setIsLoading(false);

    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("waiting", handleWaiting);
    audio.addEventListener("canplay", handleCanPlay);

    return () => {
      audio.pause();
      audio.src = "";
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("waiting", handleWaiting);
      audio.removeEventListener("canplay", handleCanPlay);
    };
  }, []);

  // 오디오 재생/일시정지 핸들러
  const handleAudioControl = useCallback(() => {
    const audio = audioRef.current;

    if (isPlaying) {
      audio.pause();
      return;
    }

    if (isPaused) {
      audio.play().catch((err) => console.error("오디오 재생 오류:", err));
      return;
    }

    // 처음 듣기 또는 다시 듣기 (제한 확인)
    if (hasPlayed && hasListenedAgain) return;

    if (audioUrl) {
      audio.currentTime = 0;
      audio
        .play()
        .then(() => {
          if (hasPlayed) setHasListenedAgain(true);
        })
        .catch((err) => console.error("오디오 재생 오류:", err));
    }
  }, [audioUrl, isPlaying, isPaused, hasPlayed, hasListenedAgain]);

  // 녹음 제어 함수
  const toggleRecording = async () => {
    if (isRecording) {
      if (!recorder) return;

      try {
        const [buffer, blob] = await recorder.stop().getMp3();
        const file = new File(buffer, `answer_${currentProblem}.mp3`, {
          type: blob.type,
        });

        if (file.size > 0) {
          setRecordedFile(file);
        } else {
          console.log("빈 녹음 파일");
        }
      } catch (error) {
        console.error("녹음 중지 오류:", error);
      } finally {
        setIsRecording(false);
      }
    } else {
      try {
        const mp3Recorder = new MicRecorder();
        await mp3Recorder.start();
        setRecorder(mp3Recorder);
        setIsRecording(true);
      } catch (error) {
        console.error("녹음 시작 오류:", error);
        alert("마이크 접근 권한이 필요합니다.");
      }
    }
  };

  // 녹음 제출 및 다음 문제 이동
  const submitRecording = async () => {
    if (!recordedFile) {
      alert("녹음을 해주세요!");
      return;
    }

    try {
      const formData = new FormData();
      formData.append("audio_file", recordedFile);

      const isLastProblem = currentProblem === maxValue;
      formData.append("is_last_problem", String(isLastProblem));

      const response = await apiClient.post(
        `/tests/${currentTest._id}/record/${currentProblemId}`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      if (response.data) {
        if (isLastProblem) {
          navigate("/tests");
        } else {
          confirm("녹음 전달에 성공했어요! 다음 문제를 풀어볼까요?");
          setCurrentProblem((prev) => prev + 1);
        }
      }
    } catch (error) {
      console.error("녹음 제출 오류:", error);
    }
  };

  // 버튼 텍스트 및 아이콘 결정
  const getListenButtonInfo = useCallback(() => {
    // 로딩 중일 때 로딩 표시 우선 반환
    if (isLoading) return { text: "로딩 중...", icon: "⏳" };
    if (isPlaying) return { text: "일시정지", icon: "⏸" };
    if (isPaused) return { text: "계속 듣기", icon: "▶️" };
    if (!hasPlayed) return { text: "문제 듣기", icon: "🎧" };
    if (!hasListenedAgain) return { text: "다시듣기", icon: "🎧" };
    return { text: "" };
  }, [isLoading, isPlaying, isPaused, hasPlayed, hasListenedAgain]);

  const isListenButtonDisabled =
    hasPlayed && hasListenedAgain && !isPaused && !isPlaying;
  const buttonInfo = getListenButtonInfo();

  return (
    <div className={styles.container}>
      <div className={styles.resize}>
        <div className={styles.numBox}>
          <span className={styles.currentNum}>{currentProblem}</span>
          <span className={styles.totalNum}> / {maxValue}</span>
        </div>
        <progress
          className={styles.progress}
          value={currentProblem}
          max={maxValue}
        ></progress>
        <img className={styles.avatarImg} src={avatar} alt="아바타" />

        <button
          className={`${styles.playBtn} ${isPlaying ? styles.pauseBtn : ""} ${
            isPaused ? styles.resumeBtn : ""
          }`}
          onClick={handleAudioControl}
          disabled={isListenButtonDisabled}
        >
          <span className={styles.headphoneIcon}>{buttonInfo.icon}</span>
          {buttonInfo.text}
        </button>
      </div>

      <div className={styles.answerBox}>
        <div className={styles.setDisplay}>
          <div className={styles.circleIcon}>
            <div className={styles.circle}></div>
            <span className={styles.micIcon}>🎤</span>
          </div>
          <span className={styles.answerText}>내 답변</span>
        </div>

        <div className={styles.animationBox}>
          {/* 녹음 중일때만 애니메이션 표시 */}
          <img
            className={
              isRecording
                ? `${styles.recording} ${styles.animationImg}`
                : `${styles.animationImg}`
            }
            src={animation}
            alt="유저 녹음중 표시"
          />

          <button
            className={styles.recordBtn}
            onClick={toggleRecording}
            disabled={isPlaying}
          >
            {isRecording ? "눌러서 녹음 종료" : "눌러서 녹음 시작"}
          </button>
        </div>
      </div>

      <button className={styles.nextButton} onClick={submitRecording}>
        다음
      </button>
    </div>
  );
}

export default TestExam;
