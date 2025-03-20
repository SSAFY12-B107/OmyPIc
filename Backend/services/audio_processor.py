# services/audio_processor.py
import io
import os
import logging
import numpy as np
import whisper
from pydub import AudioSegment
from typing import Optional, Tuple, Dict, Any
from fastapi import HTTPException

# 로깅 설정
logger = logging.getLogger(__name__)

class AudioProcessor:
    """오디오 처리 클래스: 음성 데이터 변환 및 텍스트 추출"""
    
    def __init__(self, model_name: str = "small"):
        """
        오디오 프로세서 초기화
        
        Args:
            model_name: Whisper 모델 크기 ("tiny", "base", "small", "medium", "large")
        """
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self):
        """
        지연 로딩 방식으로 Whisper 모델 초기화
        """
        if self._model is None:
            try:
                logger.info(f"Whisper {self.model_name} 모델 로딩 중...")
                self._model = whisper.load_model(self.model_name)
                logger.info(f"Whisper {self.model_name} 모델 로딩 완료")
            except Exception as e:
                logger.error(f"Whisper 모델 로딩 오류: {str(e)}")
                raise RuntimeError(f"음성 인식 모델 로딩에 실패했습니다: {str(e)}")
        return self._model
    
    def process_audio(self, audio_content: bytes) -> str:
        """
        오디오 바이트 데이터를 텍스트로 변환
        
        Args:
            audio_content: 오디오 파일 바이트 데이터
            
        Returns:
            str: 추출된 텍스트
        """
        try:
            # 1. 오디오 데이터를 numpy 배열로 변환
            audio_array = self._convert_to_audio_array(audio_content)
            
            # 2. Whisper 모델로 음성 인식
            logger.info("음성 인식 시작")
            result = self.model.transcribe(
                audio_array,
                fp16=False,
                language="en",
                task="transcribe"
            )
            
            transcribed_text = result["text"].strip()
            logger.info(f"음성 인식 완료: {transcribed_text[:50]}...")
            
            return transcribed_text
            
        except Exception as e:
            logger.error(f"음성 처리 중 오류 발생: {str(e)}", exc_info=True)
            # 구체적인 예외 유형에 따라 다른 메시지 반환
            if "파일 형식" in str(e).lower() or "format" in str(e).lower():
                raise ValueError("지원되지 않는 오디오 형식입니다. MP3 또는 WAV 파일을 사용해주세요.")
            elif "메모리" in str(e).lower() or "memory" in str(e).lower():
                raise ValueError("오디오 파일이 너무 큽니다. 최대 10MB 이하 파일을 사용해주세요.")
            else:
                raise ValueError(f"음성 처리 중 오류가 발생했습니다: {str(e)}")
    
    def _convert_to_audio_array(self, audio_content: bytes) -> np.ndarray:
        """
        오디오 바이트 데이터를 numpy 배열로 변환
        
        Args:
            audio_content: 오디오 파일 바이트 데이터
            
        Returns:
            np.ndarray: 16kHz, mono로 변환된 오디오 배열
        """
        try:
            # 1. 바이트 데이터를 pydub AudioSegment로 변환
            audio = AudioSegment.from_file(io.BytesIO(audio_content))
            
            # 2. 16kHz, mono로 변환 (Whisper 요구사항)
            audio = audio.set_frame_rate(16000).set_channels(1)
            
            # 3. 오디오 샘플을 numpy 배열로 변환
            samples = np.array(audio.get_array_of_samples())
            
            # 4. float32로 정규화
            samples = samples.astype(np.float32) / (1 << (8 * audio.sample_width - 1))
            
            return samples
            
        except Exception as e:
            logger.error(f"오디오 변환 중 오류 발생: {str(e)}", exc_info=True)
            raise ValueError(f"오디오 파일 변환에 실패했습니다: {str(e)}")