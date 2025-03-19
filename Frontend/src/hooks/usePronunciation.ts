import { useQuery } from "@tanstack/react-query";
import apiClient from "./apiClient";

// API 응답 타입 정의
interface PronunciationAudioResponse {
  audio_base64: string; // Base64 인코딩된 오디오 데이터
  audio_type: string;
  file_size_bytes: number;
  file_size_kb: number;
}

// 발음 듣기 API 훅
export const usePronunciationAudio = (scriptId: number) => {
  return useQuery<PronunciationAudioResponse, Error>({
    queryKey: ['pronunciation-audio', scriptId],
    queryFn: async () => {
      const response = await apiClient.get<PronunciationAudioResponse>(`/problems/scripts/${scriptId}/audio`);
      return response.data;
    },
    enabled: !!scriptId, // scriptId가 존재할 때만 쿼리 활성화
  });
};