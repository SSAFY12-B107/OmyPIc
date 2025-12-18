import io
import logging
import requests
import json
from pydub import AudioSegment

from core.config import settings
from core.metrics import AUDIO_PROCESS_DURATION, track_time, track_audio_size

# 로깅 설정
logger = logging.getLogger(__name__)


class AudioProcessor:
    """오디오 처리 클래스: 음성 데이터를 텍스트로 변환 (Wit.ai API 활용)"""

    def __init__(self):
        """
        오디오 프로세서 초기화

        Wit.ai API를 사용하여 음성을 텍스트로 변환합니다.
        - 무료 무제한 사용 가능
        - 한국어 지원
        """
        self.api_key = settings.WIT_AI_API_KEY
        self.base_url = "https://api.wit.ai/speech"

        if not self.api_key:
            raise ValueError("WIT_AI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

    @track_time(AUDIO_PROCESS_DURATION, {"processor": "wit_ai"})
    def process_audio(self, audio_content: bytes) -> str:
        """
        오디오 바이트 데이터를 텍스트로 변환 (Wit.ai API 활용)

        Args:
            audio_content: 오디오 파일 바이트 데이터 (MP3, WAV 등)

        Returns:
            str: 추출된 텍스트

        Raises:
            ValueError: 오디오 처리 중 오류 발생 시
        """
        try:
            # 기본적인 유효성 검사
            if not audio_content or len(audio_content) < 100:
                raise ValueError(f"오디오 데이터가 너무 작거나 유효하지 않습니다: {len(audio_content)} 바이트")

            # 오디오 데이터 크기 로깅
            logger.info(f"오디오 데이터 크기: {len(audio_content)} 바이트")

            # 오디오 크기 메트릭 추가
            track_audio_size(audio_content, "wit_ai")

            # 오디오 전처리 (필요시 MP3로 변환)
            processed_audio = self._preprocess_audio(audio_content)

            logger.info("Wit.ai 음성 인식 시작")

            # Wit.ai API 호출
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "audio/mpeg3"
            }

            response = requests.post(
                self.base_url,
                headers=headers,
                data=processed_audio,
                timeout=60
            )

            if response.status_code != 200:
                logger.error(f"Wit.ai API 오류: {response.status_code} - {response.text}")
                raise ValueError(f"Wit.ai API 오류: {response.status_code}")

            # Wit.ai는 NDJSON 형식으로 응답 (여러 줄의 JSON)
            transcribed_text = self._parse_wit_response(response.text)

            if transcribed_text:
                logger.info(f"Wit.ai 음성 인식 완료: {transcribed_text[:50]}...")
            else:
                logger.warning("Wit.ai 음성 인식 결과가 비어있습니다")
                transcribed_text = ""

            return transcribed_text

        except requests.exceptions.Timeout:
            logger.error("Wit.ai API 타임아웃")
            raise ValueError("음성 인식 서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.")
        except requests.exceptions.ConnectionError:
            logger.error("Wit.ai API 연결 실패")
            raise ValueError("음성 인식 서버에 연결할 수 없습니다. 네트워크를 확인해주세요.")
        except Exception as e:
            logger.error(f"Wit.ai 음성 처리 중 오류 발생: {str(e)}", exc_info=True)

            # 구체적인 예외 유형에 따라 다른 메시지 반환
            if "파일 형식" in str(e).lower() or "format" in str(e).lower():
                raise ValueError("지원되지 않는 오디오 형식입니다. MP3 또는 WAV 파일을 사용해주세요.")
            elif "메모리" in str(e).lower() or "memory" in str(e).lower():
                raise ValueError("오디오 파일이 너무 큽니다. 파일 크기를 줄여주세요.")
            else:
                raise ValueError(f"음성 처리 중 오류가 발생했습니다: {str(e)}")

    def _parse_wit_response(self, response_text: str) -> str:
        """
        Wit.ai NDJSON 응답을 파싱하여 최종 텍스트 추출

        Args:
            response_text: Wit.ai API 응답 텍스트 (NDJSON 형식)

        Returns:
            str: 추출된 텍스트
        """
        # Wit.ai는 여러 줄의 JSON으로 응답 (스트리밍 방식)
        # 마지막 줄에 최종 결과가 있음
        lines = response_text.strip().split('\n')

        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                result = json.loads(line)
                if 'text' in result and result['text']:
                    return result['text'].strip()
            except json.JSONDecodeError:
                continue

        return ""

    def _preprocess_audio(self, audio_content: bytes) -> bytes:
        """
        Wit.ai API 전송 전 오디오 데이터 전처리

        - MP3 형식으로 변환
        - 샘플링 레이트 최적화
        - 모노 채널로 변환

        Args:
            audio_content: 오디오 파일 바이트 데이터

        Returns:
            bytes: 전처리된 오디오 바이트 데이터 (MP3)
        """
        try:
            # pydub으로 오디오 로드
            audio = AudioSegment.from_file(io.BytesIO(audio_content))

            logger.info(f"오디오 형식: 채널={audio.channels}, 샘플레이트={audio.frame_rate}, 길이={len(audio)/1000:.1f}초")

            # 2분으로 제한 (비용 효율성)
            max_duration_ms = 2 * 60 * 1000
            if len(audio) > max_duration_ms:
                logger.info(f"오디오 길이 제한: {len(audio)/1000:.1f}초 -> {max_duration_ms/1000}초")
                audio = audio[:max_duration_ms]

            # 샘플링 레이트 최적화
            if audio.frame_rate > 16000:
                audio = audio.set_frame_rate(16000)

            # 모노로 변환
            if audio.channels > 1:
                audio = audio.set_channels(1)

            # MP3로 변환
            buffer = io.BytesIO()
            audio.export(buffer, format="mp3", bitrate="64k", parameters=["-ac", "1"])
            logger.info("오디오 전처리 완료: MP3 형식으로 변환됨")

            return buffer.getvalue()

        except Exception as e:
            logger.error(f"오디오 전처리 중 오류 발생: {str(e)}", exc_info=True)
            # 전처리 실패시 원본 반환
            logger.warning("오디오 전처리 실패, 원본 오디오 사용")
            return audio_content

    def process_audio_for_celery(self, audio_content: bytes) -> str:
        """
        Celery 태스크용 래퍼 메서드

        Args:
            audio_content: 오디오 파일 바이트 데이터

        Returns:
            str: 추출된 텍스트
        """
        return self.process_audio(audio_content)
