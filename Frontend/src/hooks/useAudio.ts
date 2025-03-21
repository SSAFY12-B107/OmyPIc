// // hooks/useAudio.ts
// import { useQuery } from '@tanstack/react-query';
// import apiClient from '../api/apiClient';

// // 오디오 응답 타입 정의
// export interface AudioResponse {
//   audio_base64: string;
//   audio_type: string;
//   file_size_bytes: number;
//   file_size_kb: number;
// }

// /**
//  * 문제에 대한 오디오 데이터를 가져오는 함수
//  * @param problem_pk 문제 ID
//  */
// const fetchAudio = async (problem_pk: string): Promise<AudioResponse> => {
//   try {
//     const response = await apiClient.get(`/tests/${problem_pk}/audio`);
//     return response.data;
//   } catch (error) {
//     console.error('오디오 데이터 가져오기 오류:', error);
//     throw error;
//   }
// };

// /**
//  * 문제에 대한 오디오 데이터를 가져오는 훅
//  * @param problem_pk 문제 ID
//  */
// export const useAudio = (problem_pk: string | undefined) => {
//   return useQuery({
//     queryKey: ['audio', problem_pk],
//     queryFn: () => {
//       if (!problem_pk) {
//         throw new Error('문제 ID가 제공되지 않았습니다');
//       }
//       return fetchAudio(problem_pk);
//     },
//     enabled: !!problem_pk,

//   });
// };

// /**
//  * Base64 오디오 데이터를 실제 오디오 URL로 변환하는 유틸리티 함수
//  */
// export const getAudioUrl = (audioData: AudioResponse | undefined): string => {
//   if (!audioData) return '';
  
//   return `data:audio/${audioData.audio_type};base64,${audioData.audio_base64}`;
// };