import styles from "./TestExam.module.css";
import avatar from "../../assets/images/avatar.png";
import animation from "../../assets/images/speaking_animate.png";
import { useTestListen } from "../../hooks/useTest";
import { useState, useRef, useEffect } from "react";
// import { RootState } from "../../store";
// import { useSelector } from 'react-redux';
import { useNavigate } from "react-router-dom";
import MicRecorder from "mic-recorder-to-mp3-fixed";
import apiClient from "../../api/apiClient";

function TestExam() {
  // 듣기 버튼 음성 관련 상태 관리
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [hasPlayed, setHasPlayed] = useState<boolean>(false); // 재생 여부 상태 추가

  // 현재 문제 번호 상태
  const [currentProblem, setCurrentProblem] = useState<number>(1);

  //사용자 답변 녹음
  const [recorder, setRecorder] = useState<MicRecorder | null>(null);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordedFile, setRecordedFile] = useState<File | null>(null);

  // 문제듣기 음성
  const audioRef = useRef<HTMLAudioElement>(new Audio());

  // 다시듣기 mutation 사용
  const listenMutation = useTestListen();

  // 리다이렉트
  const navigate = useNavigate();

  const startRecording = async () => {
    const mp3Recorder = new MicRecorder({ bitRate: 64 }); // base64

    try {
      await mp3Recorder.start();
      setRecorder(mp3Recorder);
      setIsRecording(true);
    } catch (error) {
      console.error("녹음 중 에러", error);
    }
  };

  // maxValue 임시 정의 (나중에 실제 데이터로 대체)
  const maxValue = 15; // 또는 7 (테스트 타입에 따라)

  // 녹음 중지 (파일만 저장, 제출은 하지 않음)
  const stopRecording = async () => {
    if (!recorder) return;

    try {
      //buffer 하나의 녹음을 여러 개의 작은 조각(청크)으로 나누고
      // blob 모든 청크 데이터 하나로 합합친 오디오 데이터
      const [buffer, blob] = await recorder.stop().getMp3();
      // File은 Blob을 확장하여 파일 이름과 수정 날짜 같은 추가 속성 제공
      const file = new File(buffer, "answer_recorded.mp3", {
        type: blob.type,
      });

      if (file.size === 0) {
        console.log("파일이 비어있거나 유효하지 않습니다");
        return;
      }

      setRecordedFile(file);
      setIsRecording(false);
    } catch (error) {
      console.error("녹음 중지 오류:", error);
      setIsRecording(false);
    }
  };

  // 녹음 버튼 클릭 핸들러
  const handleRecordClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // 녹음 및 API 제출 로직
  const handleRecordSubmit = async (audioFile: File) => {
    try {
      // FormData 생성
      const formData = new FormData();
      formData.append("audio", audioFile);

      // 마지막 문제인지 확인
      if (currentProblem === maxValue) {
        formData.append("status", "end");
      }

      // test_pk 임시 설정 (실제 데이터로 교체 필요)
      const test_pk = "your_test_id_here";

      // API 호출 (Content-Type 헤더 제거: FormData가 자동으로 처리)
      const response = await apiClient.post(
        `/api/tests/${test_pk}/record/${currentProblem}`,// problem_pk
        formData
      );

      // 성공 처리
      if (response.data) {
        // 다음 문제로 이동 또는 결과 페이지로 리다이렉트
        if (currentProblem < maxValue) {
          setCurrentProblem((prev) => prev + 1);
          // 상태 초기화
          setHasPlayed(false);
          setIsPlaying(false);
          setRecordedFile(null); // 녹음 파일 초기화
        } else {
          navigate(`/tests/feedback/${test_pk}/${currentProblem}`); //problem_pk
        }
      }
    } catch (error) {
      console.error("녹음 제출 오류:", error);
      // 오류 처리
    }
  };

  // 다음 버튼 클릭 핸들러 추가(onClick 활용시 마우스이벤트 객체는 ts는 타입으로 전달 못함)
  const handleNext = () => {
    if (recordedFile) {
      handleRecordSubmit(recordedFile);
    } else {
      // 그다음 currentProblem으로 컴포넌트 내 다른 정보 띄우기 ;
    }
  };

  //---------------해당 영역역 주석 무시
  // selector 필요가 없을 거 같아 ProblemAudio라고 hooks/useTest에서 ProblemAudio를 쓸 수 있지않아? 그리고 해당 데이터에 문제번호 정보도 담겨있어!
  // 그러나 처음에 페이지 접근했을 때의 음성데이터쪽에서 problem_pk 파악 가능해야 할듯

  // // Redux에서 테스트 정보 가져오기
  // const currentTest = useSelector(
  //   (state: RootState) => state.tests.currentTest
  // );

  // // 테스트 타입에 따른 최대 문제 수 설정(UI)
  // const maxValue = currentTest?.test_type ? 15 : 7;
  // --------------

  // 다시듣기 버튼 핸들러
  // 중간에 일시중지 할 경우 음원 끝까지 들을 수 있게 하기 추가 필요?
  const handleListen = async () => {
    if (isPlaying) {
      // 이미 재생 중이면 중지
      if (audioRef.current) {
        audioRef.current.pause();
        setIsPlaying(false);
      }
      return;
    }
    // 이미 재생했으면 더 이상 재생하지 않음 (버튼 비활성화됨)
    if (hasPlayed) return;

    try {
      // 현재 문제 번호를 ID로 사용
      listenMutation.mutate(currentProblem);
    } catch (error) {
      console.error("오디오 재생 오류:", error);
    }
  };

  // 다시듣기 성공 시 오디오 재생
  useEffect(() => {
    if (listenMutation.data) {
      const audio = audioRef.current;
      audio.src = listenMutation.data.audioUrl;

      audio.onplay = () => setIsPlaying(true);
      audio.onended = () => {
        setIsPlaying(false);
        setHasPlayed(true); // 재생 완료 시 재생됨 상태로 설정
      };
      audio.onerror = () => {
        setIsPlaying(false);
        console.error("오디오 재생 실패");
      };
    }
  }, [listenMutation.data]);

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
        <img className={styles.avatarImg} src={avatar} alt="" />
        <button
          className={styles.playBtn}
          onClick={handleListen}
          disabled={hasPlayed}
        >
          <span className={styles.headphoneIcon}>🎧</span>
          다시듣기
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
          {/* 녹음 중일때 애니메이션 */}

          <img
            className={styles.animationImg}
            src={animation}
            alt="유저 녹음중 표시"
          />

          {/* 녹음 중일 때 , 아닐 때 구분하기기 */}
          <button className={styles.recordBtn} onClick={handleRecordClick}>
            {isRecording ? "녹음 종료하기" : "녹음 시작하기"}
          </button>
        </div>
      </div>

      {/* <button className={styles.nextButton} onClick={handleNext}> */}
      <button className={styles.nextButton} onClick={handleNext}>
        다음
      </button>
    </div>
  );
}

export default TestExam;
