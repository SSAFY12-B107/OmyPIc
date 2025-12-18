# tests/test_audio_processor.py
"""
AudioProcessor 테스트 파일

Wit.ai STT API를 사용하는 AudioProcessor 클래스의 단위 테스트 및 통합 테스트
"""

import pytest
import json
from unittest.mock import Mock, patch
from io import BytesIO
import requests

from services.audio_processor import AudioProcessor


class TestAudioProcessorInit:
    """AudioProcessor 초기화 테스트"""

    def test_init_success_with_api_key(self):
        """정상적으로 API 키가 있을 때 초기화 성공"""
        processor = AudioProcessor()

        assert processor.api_key == "test_key"  # 환경변수에서 설정한 값
        assert processor.base_url == "https://api.wit.ai/speech"

    def test_init_fails_without_api_key(self):
        """API 키가 없을 때 ValueError 발생"""
        with patch('services.audio_processor.settings') as mock_settings:
            mock_settings.WIT_AI_API_KEY = ""

            with pytest.raises(ValueError, match="WIT_AI_API_KEY가 설정되지 않았습니다"):
                AudioProcessor()

    def test_init_fails_with_none_api_key(self):
        """API 키가 None일 때 ValueError 발생"""
        with patch('services.audio_processor.settings') as mock_settings:
            mock_settings.WIT_AI_API_KEY = None

            with pytest.raises(ValueError, match="WIT_AI_API_KEY가 설정되지 않았습니다"):
                AudioProcessor()


class TestParseWitResponse:
    """_parse_wit_response 메서드 테스트 (NDJSON 파싱)"""

    @pytest.fixture
    def processor(self):
        """테스트용 AudioProcessor 인스턴스"""
        return AudioProcessor()

    def test_parse_single_line_ndjson(self, processor):
        """단일 줄 NDJSON 응답 파싱"""
        response_text = '{"text": "안녕하세요", "is_final": true}'

        result = processor._parse_wit_response(response_text)

        assert result == "안녕하세요"

    def test_parse_multiline_ndjson(self, processor):
        """여러 줄 NDJSON 응답에서 마지막 텍스트 추출"""
        response_text = '''{"text": "안녕", "is_final": false}
{"text": "안녕하세요", "is_final": false}
{"text": "안녕하세요 반갑습니다", "is_final": true}'''

        result = processor._parse_wit_response(response_text)

        # 마지막 줄의 텍스트를 반환해야 함
        assert result == "안녕하세요 반갑습니다"

    def test_parse_empty_response(self, processor):
        """빈 응답 처리"""
        response_text = ""

        result = processor._parse_wit_response(response_text)

        assert result == ""

    def test_parse_whitespace_only_response(self, processor):
        """공백만 있는 응답 처리"""
        response_text = "   \n\n   "

        result = processor._parse_wit_response(response_text)

        assert result == ""

    def test_parse_invalid_json(self, processor):
        """잘못된 JSON 형식 처리"""
        response_text = "this is not json"

        result = processor._parse_wit_response(response_text)

        # 파싱 실패 시 빈 문자열 반환
        assert result == ""

    def test_parse_json_without_text_field(self, processor):
        """text 필드가 없는 JSON 처리"""
        response_text = '{"is_final": true, "speech": "안녕하세요"}'

        result = processor._parse_wit_response(response_text)

        # text 필드가 없으면 빈 문자열 반환
        assert result == ""

    def test_parse_json_with_empty_text(self, processor):
        """text 필드가 빈 문자열인 JSON 처리"""
        response_text = '{"text": "", "is_final": true}'

        result = processor._parse_wit_response(response_text)

        assert result == ""

    def test_parse_mixed_valid_and_invalid_lines(self, processor):
        """유효한 JSON과 무효한 JSON이 섞인 경우"""
        response_text = '''invalid line
{"text": "첫 번째 텍스트", "is_final": false}
not json either
{"text": "두 번째 텍스트", "is_final": true}'''

        result = processor._parse_wit_response(response_text)

        # 역순으로 검사하므로 마지막 유효한 텍스트 반환
        assert result == "두 번째 텍스트"

    def test_parse_with_trailing_whitespace(self, processor):
        """텍스트에 앞뒤 공백이 있는 경우 trim 처리"""
        response_text = '{"text": "  안녕하세요  ", "is_final": true}'

        result = processor._parse_wit_response(response_text)

        assert result == "안녕하세요"


class TestProcessAudio:
    """process_audio 메서드 테스트 (Mock을 활용한 API 테스트)"""

    @pytest.fixture
    def processor(self):
        """테스트용 AudioProcessor 인스턴스"""
        return AudioProcessor()

    def test_process_audio_success(self, processor, sample_audio_bytes):
        """Wit.ai API 성공 응답 Mock 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"text": "테스트 음성 인식 결과", "is_final": true}'

        with patch('services.audio_processor.requests.post', return_value=mock_response):
            with patch.object(processor, '_preprocess_audio', return_value=sample_audio_bytes):
                result = processor.process_audio(sample_audio_bytes)

        assert result == "테스트 음성 인식 결과"

    def test_process_audio_checks_audio_size(self, processor):
        """오디오 데이터가 너무 작을 때 ValueError 발생"""
        small_audio = b"tiny"  # 4 bytes only

        with pytest.raises(ValueError, match="오디오 데이터가 너무 작거나 유효하지 않습니다"):
            processor.process_audio(small_audio)

    def test_process_audio_empty_data(self, processor):
        """빈 오디오 데이터 처리"""
        empty_audio = b""

        with pytest.raises(ValueError, match="오디오 데이터가 너무 작거나 유효하지 않습니다"):
            processor.process_audio(empty_audio)

    def test_process_audio_api_timeout(self, processor, sample_audio_bytes):
        """Wit.ai API 타임아웃 처리"""
        with patch('services.audio_processor.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout()
            with patch.object(processor, '_preprocess_audio', return_value=sample_audio_bytes):

                with pytest.raises(ValueError, match="음성 인식 서버 응답 시간이 초과되었습니다"):
                    processor.process_audio(sample_audio_bytes)

    def test_process_audio_connection_error(self, processor, sample_audio_bytes):
        """Wit.ai API 연결 오류 처리"""
        with patch('services.audio_processor.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError()
            with patch.object(processor, '_preprocess_audio', return_value=sample_audio_bytes):

                with pytest.raises(ValueError, match="음성 인식 서버에 연결할 수 없습니다"):
                    processor.process_audio(sample_audio_bytes)

    def test_process_audio_api_400_error(self, processor, sample_audio_bytes):
        """Wit.ai API 400 에러 처리 (잘못된 요청)"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with patch('services.audio_processor.requests.post', return_value=mock_response):
            with patch.object(processor, '_preprocess_audio', return_value=sample_audio_bytes):

                with pytest.raises(ValueError, match="Wit.ai API 오류: 400"):
                    processor.process_audio(sample_audio_bytes)

    def test_process_audio_api_500_error(self, processor, sample_audio_bytes):
        """Wit.ai API 500 에러 처리 (서버 오류)"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch('services.audio_processor.requests.post', return_value=mock_response):
            with patch.object(processor, '_preprocess_audio', return_value=sample_audio_bytes):

                with pytest.raises(ValueError, match="Wit.ai API 오류: 500"):
                    processor.process_audio(sample_audio_bytes)

    def test_process_audio_empty_transcription(self, processor, sample_audio_bytes):
        """음성 인식 결과가 비어있는 경우"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"text": "", "is_final": true}'

        with patch('services.audio_processor.requests.post', return_value=mock_response):
            with patch.object(processor, '_preprocess_audio', return_value=sample_audio_bytes):
                result = processor.process_audio(sample_audio_bytes)

        # 빈 문자열 반환
        assert result == ""

    def test_process_audio_calls_preprocess(self, processor, sample_audio_bytes):
        """process_audio가 _preprocess_audio를 호출하는지 확인"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"text": "테스트", "is_final": true}'

        with patch('services.audio_processor.requests.post', return_value=mock_response):
            with patch.object(processor, '_preprocess_audio', return_value=sample_audio_bytes) as mock_preprocess:
                processor.process_audio(sample_audio_bytes)

                # _preprocess_audio가 호출되었는지 확인
                mock_preprocess.assert_called_once_with(sample_audio_bytes)

    def test_process_audio_sends_correct_headers(self, processor, sample_audio_bytes):
        """Wit.ai API 요청 시 올바른 헤더를 전송하는지 확인"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"text": "테스트", "is_final": true}'

        with patch('services.audio_processor.requests.post', return_value=mock_response) as mock_post:
            with patch.object(processor, '_preprocess_audio', return_value=sample_audio_bytes):
                processor.process_audio(sample_audio_bytes)

                # requests.post 호출 시 전달된 인자 확인
                call_args = mock_post.call_args
                headers = call_args.kwargs['headers']

                assert headers['Authorization'] == 'Bearer test_key'  # 환경변수에서 설정한 값
                assert headers['Content-Type'] == 'audio/mpeg3'

    def test_process_audio_unsupported_format_error(self, processor, sample_audio_bytes):
        """지원되지 않는 오디오 형식 오류 처리"""
        with patch('services.audio_processor.requests.post') as mock_post:
            mock_post.side_effect = Exception("unsupported audio format")
            with patch.object(processor, '_preprocess_audio', return_value=sample_audio_bytes):

                with pytest.raises(ValueError, match="지원되지 않는 오디오 형식입니다"):
                    processor.process_audio(sample_audio_bytes)

    def test_process_audio_memory_error(self, processor, sample_audio_bytes):
        """메모리 오류 처리"""
        with patch('services.audio_processor.requests.post') as mock_post:
            mock_post.side_effect = Exception("memory overflow")
            with patch.object(processor, '_preprocess_audio', return_value=sample_audio_bytes):

                with pytest.raises(ValueError, match="오디오 파일이 너무 큽니다"):
                    processor.process_audio(sample_audio_bytes)


class TestPreprocessAudio:
    """_preprocess_audio 메서드 테스트"""

    @pytest.fixture
    def processor(self):
        """테스트용 AudioProcessor 인스턴스"""
        return AudioProcessor()

    def test_preprocess_audio_fallback_on_error(self, processor):
        """전처리 실패 시 원본 오디오 반환"""
        original_audio = b"original_audio_data" * 100

        # AudioSegment.from_file이 실패하도록 Mock
        with patch('services.audio_processor.AudioSegment.from_file') as mock_from_file:
            mock_from_file.side_effect = Exception("Audio processing failed")

            result = processor._preprocess_audio(original_audio)

        # 실패 시 원본 반환
        assert result == original_audio

    def test_preprocess_audio_limits_duration(self, processor):
        """2분 이상의 오디오를 2분으로 제한하는지 테스트"""
        sample_audio = b"long_audio" * 100

        # 3분짜리 오디오 Mock
        mock_audio = Mock()
        mock_audio.channels = 1
        mock_audio.frame_rate = 16000
        mock_audio.__len__ = Mock(return_value=180000)  # 3분 = 180초 = 180000ms

        # 슬라이싱된 오디오 Mock
        mock_sliced_audio = Mock()
        mock_sliced_audio.channels = 1
        mock_sliced_audio.frame_rate = 16000
        mock_sliced_audio.export = Mock()
        mock_audio.__getitem__ = Mock(return_value=mock_sliced_audio)

        mock_buffer = BytesIO(b"processed_audio")

        with patch('services.audio_processor.AudioSegment.from_file', return_value=mock_audio):
            with patch('services.audio_processor.io.BytesIO', return_value=mock_buffer):
                processor._preprocess_audio(sample_audio)

                # 2분(120000ms)으로 슬라이싱되었는지 확인
                mock_audio.__getitem__.assert_called_once_with(slice(None, 120000, None))


class TestProcessAudioForCelery:
    """process_audio_for_celery 메서드 테스트"""

    @pytest.fixture
    def processor(self):
        """테스트용 AudioProcessor 인스턴스"""
        return AudioProcessor()

    def test_celery_wrapper_calls_process_audio(self, processor):
        """Celery 래퍼가 process_audio를 호출하는지 확인"""
        sample_audio = b"audio_data" * 100
        expected_result = "음성 인식 결과"

        with patch.object(processor, 'process_audio', return_value=expected_result) as mock_process:
            result = processor.process_audio_for_celery(sample_audio)

            # process_audio가 호출되었는지 확인
            mock_process.assert_called_once_with(sample_audio)
            assert result == expected_result
