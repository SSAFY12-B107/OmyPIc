import { useQuery } from "@tanstack/react-query";
import apiClient from "../api/apiClient";

// API 응답 타입 정의
interface PronunciationAudioResponse {
  audio_base64: string; // Base64 인코딩된 오디오 데이터
  audio_type: string;
  file_size_bytes: number;
  file_size_kb: number;
}

// 발음 듣기 API 훅
export const usePronunciationAudio = (scriptId: string | null) => { // number에서 string으로 변경
  return useQuery<PronunciationAudioResponse, Error>({
    queryKey: ['pronunciation-audio', scriptId],
    queryFn: async () => {
      const response = await apiClient.post<PronunciationAudioResponse>(`/problems/scripts/${scriptId}/audio`);
      return response.data;
    },
    enabled: !!scriptId, // scriptId가 존재할 때만 쿼리 활성화
    staleTime: 1000 * 60 * 10, // 10분 동안 데이터를 "신선한" 상태로 유지
    gcTime: 1000 * 60 * 60, // 1시간 동안 캐시 유지 (이전 cacheTime)
    refetchOnWindowFocus: false, // 창 포커스 시 재요청 방지
    refetchOnMount: false, // 컴포넌트 마운트 시 재요청 방지
  });
};