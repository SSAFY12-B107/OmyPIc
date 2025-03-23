// mp3 파일 타입지정정
declare module 'mic-recorder-to-mp3-fixed' {
    export default class MicRecorder {
      constructor(options?: { bitRate?: number; });
      start(): Promise<void>;
      stop(): {
        getMp3(): Promise<[Blob[], Blob]>;
      };
    }
  }