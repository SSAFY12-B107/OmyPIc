import io
import logging
from pydub import AudioSegment
from groq import Groq
from api.deps import get_next_groq_key

from core.metrics import AUDIO_PROCESS_DURATION, track_time, track_audio_size, AUDIO_SIZE_VS_PROCESS_TIME

# 로깅 설정
logger = logging.getLogger(__name__)

class AudioProcessor:
    """오디오 처리 클래스: 음성 데이터 변환 및 텍스트 추출 (Groq API 활용)"""
    
    def __init__(self, model_name: str = "whisper-large-v3"):
        """
        오디오 프로세서 초기화
        
        Args:
            model_name: Groq Whisper 모델 이름 (기본값: "whisper-large-v3")
        """
        self.model_name = model_name
        self._client = None
    
    @property
    def client(self):
        """
        지연 로딩 방식으로 Groq 클라이언트 초기화
        """
        if self._client is None:
            try:
                # api/deps.py의 get_next_groq_key() 함수를 사용해 API 키 순환
                api_key = get_next_groq_key()
                if not api_key:
                    raise ValueError("Groq API 키가 설정되지 않았습니다.")
                
                logger.info("Groq 클라이언트 초기화 중...")
                self._client = Groq(api_key=api_key)
                logger.info("Groq 클라이언트 초기화 완료")
            except Exception as e:
                logger.error(f"Groq 클라이언트 초기화 오류: {str(e)}")
                raise RuntimeError(f"Groq API 연결에 실패했습니다: {str(e)}")
        return self._client
    
    @track_time(AUDIO_PROCESS_DURATION, {"processor": "groq"})
    def process_audio(self, audio_content: bytes) -> str:
        """
        오디오 바이트 데이터를 텍스트로 변환 (Groq API 활용)
        
        Args:
            audio_content: 오디오 파일 바이트 데이터
        
        Returns:
            str: 추출된 텍스트
        """
        try:
            # 기본적인 유효성 검사
            if not audio_content or len(audio_content) < 100:
                raise ValueError(f"오디오 데이터가 너무 작거나 유효하지 않습니다: {len(audio_content)} 바이트")
            
            # 오디오 데이터 크기 로깅
            logger.info(f"오디오 데이터 크기: {len(audio_content)} 바이트")
            
            # 오디오 크기 메트릭 추가
            track_audio_size(audio_content, "groq")

            # 임시 파일 생성 - 확장자를 명시적으로 지정
            temp_file_name = "temp_audio_file.mp3"
            
            logger.info(f"Groq {self.model_name} 모델로 음성 인식 시작")
            
            # Groq API 호출 - 파일 이름에 확장자 포함
            transcription = self.client.audio.transcriptions.create(
                file=(temp_file_name, audio_content),
                model=self.model_name,
                response_format="text"
            )
            
            # 응답에서 텍스트 추출 (response_format="text"일 경우 직접 문자열 반환)
            transcribed_text = transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
            logger.info(f"Groq 음성 인식 완료: {transcribed_text[:50]}...")
            
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Groq 음성 처리 중 오류 발생: {str(e)}", exc_info=True)
            # 구체적인 예외 유형에 따라 다른 메시지 반환
            if "파일 형식" in str(e).lower() or "format" in str(e).lower():
                raise ValueError("지원되지 않는 오디오 형식입니다. MP3 또는 WAV 파일을 사용해주세요.")
            elif "메모리" in str(e).lower() or "memory" in str(e).lower():
                raise ValueError("오디오 파일이 너무 큽니다. 최대 25MB 이하 파일을 사용해주세요.")
            elif "api" in str(e).lower() or "key" in str(e).lower() or "auth" in str(e).lower():
                raise ValueError("Groq API 연결에 문제가 발생했습니다. 관리자에게 문의해주세요.")
            else:
                raise ValueError(f"음성 처리 중 오류가 발생했습니다: {str(e)}")
            
    @track_time(AUDIO_PROCESS_DURATION, {"processor": "groq_optimized"})
    def process_audio_for_celery(self, audio_content: bytes) -> str:
        return self.process_audio(audio_content)


class FastAudioProcessor(AudioProcessor):
    """최적화된 설정으로 Groq Whisper 모델을 사용하는 오디오 프로세서"""
    
    def __init__(self, model_name: str = "whisper-large-v3"):
        """
        최적화 오디오 프로세서 초기화
        
        Args:
            model_name: Groq Whisper 모델 이름 (기본값: "whisper-large-v3")
        """
        super().__init__(model_name)
    
    @track_time(AUDIO_PROCESS_DURATION, {"processor": "groq_optimized"})
    def process_audio_fast(self, audio_content: bytes) -> str:
        """
        최적화된 설정으로 오디오 바이트 데이터를 텍스트로 변환
        
        Args:
            audio_content: 오디오 파일 바이트 데이터
            
        Returns:
            str: 추출된 텍스트
        """
        try:

            # 오디오 크기 메트릭 추가
            track_audio_size(audio_content, "groq_optimized")


            # 1. 필요시 오디오 데이터 전처리
            processed_audio = self._preprocess_audio(audio_content)
            
            # 2. Groq API로 음성 인식
            logger.info(f"최적화 Groq 음성 인식 시작 (모델: {self.model_name})")
            
            # 임시 파일 이름 설정
            temp_file_name = "temp_audio_file"
            
            # Groq API 호출 - 확장자를 명시적으로 지정
            transcription = self.client.audio.transcriptions.create(
                file=(f"temp_audio_file.mp3", processed_audio),
                model=self.model_name,
                response_format="text"
            )
            
            # 응답에서 텍스트 추출 (response_format="text"일 경우 직접 문자열 반환)
            transcribed_text = transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
            logger.info(f"최적화 Groq 음성 인식 완료: {transcribed_text[:50]}...")
            
            return transcribed_text
            
        except Exception as e:
            logger.error(f"최적화 Groq 음성 처리 중 오류 발생: {str(e)}", exc_info=True)
            if "파일 형식" in str(e).lower() or "format" in str(e).lower():
                raise ValueError("지원되지 않는 오디오 형식입니다. MP3 또는 WAV 파일을 사용해주세요.")
            elif "메모리" in str(e).lower() or "memory" in str(e).lower():
                raise ValueError("오디오 파일이 너무 큽니다. 최대 25MB 이하 파일을 사용해주세요.")
            elif "api" in str(e).lower() or "key" in str(e).lower() or "auth" in str(e).lower():
                raise ValueError("Groq API 연결에 문제가 발생했습니다. 관리자에게 문의해주세요.")
            else:
                raise ValueError(f"최적화 음성 처리 중 오류가 발생했습니다: {str(e)}")
    
    def _preprocess_audio(self, audio_content: bytes) -> bytes:
        """
        Groq API 전송 전 오디오 데이터 전처리
        
        Args:
            audio_content: 오디오 파일 바이트 데이터
            
        Returns:
            bytes: 전처리된 오디오 바이트 데이터
        """
        try:
            # 필요한 경우 오디오 길이 제한
            audio = AudioSegment.from_file(io.BytesIO(audio_content))
            
            # 파일 형식이 지원되는지 확인 (로그 기록용)
            original_format = audio.channels
            logger.info(f"오디오 형식: 채널={audio.channels}, 샘플레이트={audio.frame_rate}, 길이={len(audio)/1000:.1f}초")
            
            # 2분으로 제한 (Groq API는 더 긴 오디오도 처리 가능하지만, 비용 효율성을 위해)
            max_duration_ms = 2 * 60 * 1000
            if len(audio) > max_duration_ms:
                logger.info(f"오디오 길이 제한: {len(audio)/1000:.1f}초 -> {max_duration_ms/1000}초")
                audio = audio[:max_duration_ms]
            
            # 샘플링 레이트 최적화 (Groq API 권장 형식으로)
            if audio.frame_rate > 48000:
                audio = audio.set_frame_rate(48000)
            
            # 채널 수 최적화 (모노로 변환)
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # 처리된 오디오를 바이트로 변환 - 명시적으로 MP3 형식 지정
            buffer = io.BytesIO()
            audio.export(buffer, format="mp3", bitrate="128k", parameters=["-ac", "1"])
            logger.info("오디오 전처리 완료: MP3 형식으로 변환됨")
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"오디오 전처리 중 오류 발생: {str(e)}", exc_info=True)
            # 전처리 실패시 원본 반환
            logger.warning("오디오 전처리 실패, 원본 오디오 사용")
            return audio_content