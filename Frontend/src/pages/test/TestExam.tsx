import { useState, useRef, useEffect, useCallback } from "react";
import styles from "./TestExam.module.css";
import avatar from "@/assets/images/avatar.png";
import animation from "@/assets/images/speaking_animate.png";
import { RootState } from "@/store/store";
import { useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { useTestEndAction } from "@/contexts/HeaderContext";
import MicRecorder from "mic-recorder-to-mp3-fixed";
import apiClient from "@/api/apiClient";
import FeedbackModal from "@/components/test/FeedbackModal";

function TestExam() {
  console.log("이동완료(?)");
  // 컴포넌트 최상단에 문제 mp3 캐시 객체 선언
  const audioCache = useRef<Record<string, HTMLAudioElement>>({}).current;

  // 문제 모음 가져오기(리덕스)
  const currentTest = useSelector((state: RootState) =>
    state && state.tests ? state.tests.currentTest : null
  );

  // 단일 랜덤 문제 가져오기(리덕스)
  const currentSingleProblem = useSelector((state: RootState) =>
    state && state.tests ? state.tests.currentSingleProblem : null
  );

  // 랜덤 문제 여부 확인
  const isRandomProblem = useSelector((state: RootState) =>
    state && state.tests ? state.tests.isRandomProblem : false
  );

  const state = useSelector((state: RootState) => state);

  console.log("전체 Redux 상태:", state);
  console.log("currentTest 상태:", currentTest);
  console.log("currentSingleProblem 상태:", currentSingleProblem);
  console.log("isRandomProblem 상태:", isRandomProblem);
  console.log("audioCache입니다", audioCache);

  // 테스트 타입에 따른 최대 문제 수 설정
  const maxValue = isRandomProblem ? 1 : currentTest?.test_type == 0 ? 15 : 3;
  console.log("maxValue", maxValue);
  console.log("currentTest?.test_type", currentTest?.test_type);
  console.log("currentTest", currentTest);

  // 문제번호 관리(ui)
  const [currentProblem, setCurrentProblem] = useState<number>(1);

  // 한문제 평가 피드백 저장
  const [randomProblemResult, setRandomProblemResult] = useState<any>(null);

  // 오디오 상태
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [hasPlayed, setHasPlayed] = useState<boolean>(false);
  const [hasListenedAgain, setHasListenedAgain] = useState<boolean>(false);

  // 녹음 상태
  const [recorder, setRecorder] = useState<MicRecorder | null>(null);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordedFile, setRecordedFile] = useState<File | null>(null);

  // 녹음 타이머 관련 상태 추가
  const recordingTimeRef = useRef<number>(0);
  const timeDisplayRef = useRef<HTMLSpanElement>(null);
  const timerRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);

  // 랜덤문제 모달창
  const [isOpen, setIsOpen] = useState<boolean>(false);

  // 로딩 상태 관리 추가
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [randomEvaluationLoading, setRandomEvaluationLoading] =
    useState<boolean>(false);

  const onClose = () => {
    setIsOpen(!isOpen);
  };

  const navigate = useNavigate();

  // 테스트 종료 처리 함수를 useCallback으로 메모이제이션
  const handleEndTest = useCallback(async () => {
    try {
      // 랜덤 문제와 일반 테스트 구분
      const testId = isRandomProblem
        ? currentSingleProblem?.test_id
        : currentTest?._id;

      if (!testId) {
        console.error("테스트 ID가 없습니다.");
        navigate("/tests");
        return;
      }

      // 테스트 종료 API 호출
      await apiClient.delete(`/tests/${testId}`);

      // 성공적으로 API 호출 후 테스트 목록 페이지로 이동
      navigate("/tests");
    } catch (error) {
      console.error("테스트 종료 오류:", error);
      // 오류가 발생하더라도 페이지 이동
      navigate("/tests");
    }
  }, [
    currentTest?._id,
    currentSingleProblem?.test_id,
    isRandomProblem,
    navigate,
  ]);

  // 테스트 종료 함수 등록
  useTestEndAction(handleEndTest);

  //응시 페이지 진입 시 Audio 객체 미리 생성
  useEffect(() => {
    console.log("currentTest", currentTest);
    console.log("currentSingleProblem", currentSingleProblem);

    // 랜덤 문제인 경우
    if (isRandomProblem && currentSingleProblem?.audio_s3_url) {
      if (!audioCache[currentProblem]) {
        const correctedUrl = currentSingleProblem.audio_s3_url.replace(
          "ap-northeast-2",
          "us-east-2"
        );
        const audioObj = new Audio(correctedUrl);
        audioCache[currentProblem] = audioObj;
        console.log(`랜덤 문제 오디오 객체 생성됨:`, audioObj);
      }
    }
    // 일반 테스트인 경우
    else if (currentTest?.problem_data) {
      for (
        let i = currentProblem;
        i < Math.min(currentProblem + 3, maxValue + 1);
        i++
      ) {
        const problemData = currentTest.problem_data[i];
        console.log("problemData", problemData);
        if (problemData && problemData.audio_s3_url) {
          if (!audioCache[i]) {
            const correctedUrl = problemData.audio_s3_url.replace(
              "ap-northeast-2",
              "us-east-2"
            );
            const audioObj = new Audio(correctedUrl);
            audioCache[i] = audioObj;
            console.log(`오디오 캐시 저장됨 [${i}]:`, audioObj);
          }
        }
      }
    }
  }, [
    currentProblem,
    currentTest,
    currentSingleProblem,
    isRandomProblem,
    maxValue,
  ]);

  useEffect(() => {
    // 문제 번호가 변경될 때 재생 상태 초기화
    setIsPlaying(false);
    setIsPaused(false);
    setHasPlayed(false);
    setHasListenedAgain(false);
    // 녹음 파일도 초기화
    setRecordedFile(null);
  }, [currentProblem]);

  // 오디오 이벤트 설정(ui 설정정)
  useEffect(() => {
    const audio = audioCache[currentProblem];
    if (audioCache) console.log("audioCache", audioCache);

    if (!audio) return;

    const handleEnded = () => {
      setIsPlaying(false);
      setIsPaused(false);
      setHasPlayed(true);
    };

    //콜백함수(조건 아래 실행)
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

    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);

    return () => {
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);
    };
  }, [currentProblem, audioCache]);

  // 컴포넌트 언마운트 시에만 오디오 정리
  useEffect(() => {
    return () => {
      // 이 함수는 컴포넌트가 언마운트될 때만 호출됩니다
      // 페이지를 완전히 나갈 때만 실행
      Object.values(audioCache).forEach((audio) => {
        if (audio) {
          audio.pause();
          audio.currentTime = 0;
        }
      });
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []); // 빈 의존성 배열: 마운트/언마운트 시에만 실행

  // 시간 형식 변환 함수 (초 -> MM:SS)
  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, "0")}:${remainingSeconds
      .toString()
      .padStart(2, "0")}`;
  };
  // 오디오 재생/일시정지 핸들러
  const handleAudioControl = useCallback(() => {
    const audio = audioCache[currentProblem];

    if (isPlaying) {
      audio.pause();
      console.log("pause");
      return;
    }

    if (isPaused) {
      audio.play().catch((err) => console.error("오디오 재생 오류:", err));
      return;
    }

    // 처음 듣기 또는 다시 듣기 (제한 확인)
    if (hasPlayed && hasListenedAgain) return;

    if (audio) {
      audio.currentTime = 0;
      audio
        .play()
        .then(() => {
          if (hasPlayed) setHasListenedAgain(true);
        })
        .catch((err) => console.error("오디오 재생 오류:", err));
    }
  }, [
    isPlaying,
    isPaused,
    hasPlayed,
    hasListenedAgain,
    audioCache,
    currentProblem,
  ]);

  // 녹음 제어 함수
  const toggleRecording = async () => {
    if (isRecording) {
      if (!recorder) return;

      try {
        // 타이머 중지
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
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
        const mp3Recorder = new MicRecorder({
          bitRate: 64, // 매우 낮은 비트레이트 설정
          channels: 1, // 모노 채널 사용
        } as any);
        await mp3Recorder.start();
        setRecorder(mp3Recorder);
        setIsRecording(true);

        // 녹음 시작 시간 저장
        // 녹음 시작 시간 저장
        startTimeRef.current = Date.now();
        recordingTimeRef.current = 0;

        // 시간 표시 초기화
        if (timeDisplayRef.current) {
          timeDisplayRef.current.textContent = "00:00";
        }

        // 타이머 시작 - DOM을 직접 업데이트
        timerRef.current = window.setInterval(() => {
          const elapsedSeconds = Math.floor(
            (Date.now() - startTimeRef.current) / 1000
          );
          recordingTimeRef.current = elapsedSeconds;

          if (timeDisplayRef.current) {
            const minutes = Math.floor(elapsedSeconds / 60);
            const remainingSeconds = elapsedSeconds % 60;
            timeDisplayRef.current.textContent = `${minutes
              .toString()
              .padStart(2, "0")}:${remainingSeconds
              .toString()
              .padStart(2, "0")}`;
          }
        }, 50);
      } catch (error) {
        console.error("녹음 시작 오류:", error);
        alert("마이크 접근 권한이 필요합니다.");
      }
    }
  };

  // 녹음 제출 및 다음 문제 이동
  const submitRecording = async () => {
    if (!recordedFile || isSubmitting) {
      return;
    }

    setIsSubmitting(true);

    try {
      const isLastProblem = currentProblem === maxValue;
      const formData = new FormData();
      formData.append("audio_file", recordedFile);

      let response;

      // 랜덤 문제인 경우
      if (isRandomProblem && currentSingleProblem) {
        console.log("랜덤 문제 제출:", currentSingleProblem.test_id);

        // 랜덤 문제일 때만 로딩 상태 설정 및 모달 열기
        setRandomEvaluationLoading(true);
        setIsOpen(true); // 모달 먼저 열기

        // 수정된 부분: problem_id 대신 test_id 사용
        formData.append("test_id", currentSingleProblem.test_id);

        response = await apiClient.post(
          "tests/random-problem/evaluate",
          formData,
          {
            headers: { "Content-Type": "multipart/form-data" },
          }
        );

        // 랜덤 문제 결과만 저장
        if (response) {
          console.log("단일평가 피드백", response?.data);
          setRandomProblemResult(response.data);
        }
      }
      // 일반 테스트 문제
      else if (currentTest) {
        // 현재 문제 ID 가져오기
        const currentProblemId =
          currentTest?.problem_data[currentProblem]?.problem_id;

        if (!currentProblemId) {
          console.error("문제 ID를 찾을 수 없습니다.");
          return;
        }

        formData.append("is_last_problem", String(isLastProblem));
        console.log("마지막 문제 제출했습니다", isLastProblem);

        response = await apiClient.post(
          `/tests/${currentTest._id}/record/${currentProblemId}`,
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        );
      }

      if (response?.data) {
        // 랜덤 문제가 아니고 마지막 문제인 경우
        if (!isRandomProblem && isLastProblem && currentTest) {
          // 메인 페이지로 이동하면서 폴링 시작을 위한 상태 전달
          alert("시험 응시 완료!🐧");
          navigate("/tests", {
            state: {
              recentTestId: currentTest._id,
              feedbackReady: false, // 아직 피드백이 준비되지 않았음
              testType: currentTest.test_type, // test_type도 함께 전달
            },
          });
        } else if (!isRandomProblem && !isLastProblem) {
          confirm("녹음 전달에 성공했어요! 다음 문제를 풀어볼까요?");
          setCurrentProblem((prev) => prev + 1);
        }
      }
    } catch (error) {
      console.error("녹음 제출 오류:", error);
    } finally {
      // 랜덤 문제 상태 설정 해제
      if (isRandomProblem) {
        setRandomEvaluationLoading(false);
      }
      setIsSubmitting(false);

    }
  };

  // 버튼 텍스트 및 아이콘 결정
  const getListenButtonInfo = useCallback(() => {
    // 로딩 중일 때 로딩 표시 우선 반환
    if (isPlaying) return { text: "일시정지", icon: "⏸" };
    if (isPaused) return { text: "계속 듣기", icon: "▶️" };
    if (!hasPlayed) return { text: "문제 듣기", icon: "🎧" };
    if (!hasListenedAgain) return { text: "다시듣기", icon: "🎧" };
    return { text: "-" };
  }, [isPlaying, isPaused, hasPlayed, hasListenedAgain]);

  const isListenButtonDisabled =
    hasPlayed && hasListenedAgain && !isPaused && !isPlaying;
  const buttonInfo = getListenButtonInfo();

  return (
    <div className={styles.container}>
      <FeedbackModal
        isOpen={isOpen}
        onClose={onClose}
        data={randomProblemResult}
        isLoading={randomEvaluationLoading}
      />

      <div className={styles.resize}>
        {/* 프로그레스 바는 랜덤 문제가 아닐 때만 표시 */}
        {!isRandomProblem && (
          <>
            <div className={styles.numBox}>
              <span className={styles.currentNum}>{currentProblem}</span>
              <span className={styles.totalNum}> / {maxValue}</span>
            </div>
            <progress
              className={styles.progress}
              value={currentProblem}
              max={maxValue}
            ></progress>
          </>
        )}

        <img className={styles.avatarImg} src={avatar} alt="아바타" />

        <button
          className={`${styles.playBtn} ${isPlaying ? styles.pauseBtn : ""} ${
            isPaused ? styles.resumeBtn : ""
          }`}
          onClick={handleAudioControl}
          disabled={isListenButtonDisabled || isRecording}
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

          {/* 녹음 시간 표시 추가 */}
          <span ref={timeDisplayRef} className={styles.recordingTime}>
          </span>
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
            disabled={isPlaying || isSubmitting} // 오디오 재생 중이거나 제출 중일 때 비활성화
          >
            {isRecording ? "눌러서 녹음 종료" : "눌러서 녹음 시작"}
          </button>
        </div>
      </div>

      <button
        className={
          recordedFile && !isSubmitting
            ? styles.nextButton
            : `${styles.nextButton} ${styles.disabledButton}`
        }
        onClick={submitRecording}
        disabled={!recordedFile || isSubmitting} // 녹음 파일이 없거나 제출 중일 때 비활성화
      >
        {isSubmitting ? "제출 중...🐧" : "다음"}
      </button>
    </div>
  );
}

export default TestExam;
