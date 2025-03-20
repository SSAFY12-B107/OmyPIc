import { useQuery, useMutation } from "@tanstack/react-query";
import apiClient from "../api/apiClient";

// export interface Test {
//   // 응답 데이터에 따라 설정
// }


// // 모의고사 응시(종류에 따라 생성 버튼)
// export const useTestPost = () => {
//   //첫번째 인자 : API 호출이 성공했을 때 반환되는 데이터의 타입
//   return useMutation<Test, Error, boolean>({
//     mutationFn: async (test_type: boolean) => {
//       const { data } = await apiClient.post<Test>(`/tests/${test_type}`);
//       return data;
//     },
//     onSuccess: (data) => {
//       // 성공 시 캐시 업데이트 또는 다른 작업 수행
//       console.log("모의고사 생성 완료", data);
//     },
//     onError: (error) => {
//       console.error("모의고사 생성 중 오류 발생:", error);
//     },
//   });
// };


// 문제 음성 (다시듣기 기능)
export interface ProblemAudio  {
  problem_pk : number,
  audioUrl : string
  // 응답 데이터에 따라 설정(MP3 파일 받아오기)
}

// 문제 듣기 버튼
export const useTestListen = () => {
  return useMutation<ProblemAudio , Error, number>({
    mutationFn: async (problem_pk: number) => {
      const { data } = await apiClient.post<ProblemAudio>(
        `/tests/${problem_pk}/audio`
      );
      return data
    },
    onSuccess: (data) => {
        console.log('질문듣기', data)
    },
    onError : (error) => {
        console.error('질문듣기 오류 발생', error)
    }
  });
};
