interface PronunciationAudioResponse {
    audio_base64: string;
    audio_type: string;
    file_size_bytes: number;
    file_size_kb: number;
}
export declare const usePronunciationAudio: (scriptId: number) => import("@tanstack/react-query").UseQueryResult<PronunciationAudioResponse, Error>;
export {};
