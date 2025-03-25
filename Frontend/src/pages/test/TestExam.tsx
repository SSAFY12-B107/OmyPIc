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
import { useQueryClient } from "@tanstack/react-query";

function TestExam() {
  const queryClient = useQueryClient();

  // 컴포넌트 최상단에 문제 mp3 캐시 객체 선언
  const audioCache = useRef<Record<string, HTMLAudioElement>>({}).current;

  // 문제 모음 가져오기(리덕스)
  const currentTest = useSelector((state: RootState) =>
    state && state.tests ? state.tests.currentTest : undefined
  );

  const state = useSelector((state: RootState) => state);

  console.log("전체 Redux 상태:", state);
  console.log("전체 currentTest 상태:", currentTest);
  console.log("audioCache입니다", audioCache);

  // 테스트 타입에 따른 최대 문제 수 설정
  const maxValue =
    currentTest?.test_type == 1 ? 15 : currentTest?.test_type == 0 ? 7 : 1;

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
      if (!currentTest?._id) {
        console.error("테스트 ID가 없습니다.");
        navigate("/tests");
        return;
      }

      // 테스트 종료 API 호출
      await apiClient.delete(`/tests/${currentTest._id}`);

      // 성공적으로 API 호출 후 테스트 목록 페이지로 이동
      navigate("/tests");
    } catch (error) {
      console.error("테스트 종료 오류:", error);
      // 오류가 발생하더라도 페이지 이동
      navigate("/tests");
    }
  }, [currentTest?._id, navigate]);

  // 테스트 종료 함수 등록
  useTestEndAction(handleEndTest);

  //응시 페이지 진입 시 Audio 객체 미리 생성
  useEffect(() => {
    console.log("currentTest", currentTest);

    if (currentTest?.audio_s3_url) {
      if (currentTest.audio_s3_url) {
        const correctedUrl = currentTest.audio_s3_url.replace(
          "ap-northeast-2",
          "us-east-2"
        );
        const audioObj = new Audio(correctedUrl);
        audioCache[currentProblem] = audioObj;
        console.log(`오디오 객체 생성됨:`, audioObj);
      }
    } else if (currentTest?.problem_data) {
      // test_type이 1 또는 0일 때 기존 방식으로 처리
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
  }, [currentProblem, currentTest]);

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
  }, [currentProblem]);

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
    };
  }, []); // 빈 의존성 배열: 마운트/언마운트 시에만 실행

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
  }, [isPlaying, isPaused, hasPlayed, hasListenedAgain]);

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
    if (!recordedFile || isSubmitting) {
      return;
    }

    setIsSubmitting(true);

    try {
      const isLastProblem = currentProblem === maxValue;
      let random = 1;
      const formData = new FormData();
      formData.append("audio_file", recordedFile);

      let response;

      // currentTest.problem_id가 있는 경우 (랜덤 문제)
      if (currentTest?.problem_id) {
        console.log("currentTest?.problem_id", currentTest?.problem_id);

        // 랜덤 문제일 때만 로딩 상태 설정 및 모달 열기
        setRandomEvaluationLoading(true);
        setIsOpen(true); // 모달 먼저 열기

        // params 대신 FormData에 직접 추가
        formData.append("problem_id", currentTest.problem_id);

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
      // 기존 로직 (일반 문제)
      else {
        random = 0;

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
        // 모의고사 문제일 때 고려
        if (isLastProblem && random === 0) {
          // 마지막 문제 제출 시 히스토리 쿼리 무효화 후 navigate
          queryClient.invalidateQueries({ queryKey: ['userHistory'] });
          navigate("/tests");
        } else if (!isLastProblem && random === 0) {
          confirm("녹음 전달에 성공했어요! 다음 문제를 풀어볼까요?");
          setCurrentProblem((prev) => prev + 1);
        }
      }
    } catch (error) {
      console.error("녹음 제출 오류:", error);
    } finally {
      // test_type에 따른 로딩 상태 해제
      if (currentTest?.problem_id) {
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
        {currentTest?.problem_data ? (
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
        ) : null}

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
