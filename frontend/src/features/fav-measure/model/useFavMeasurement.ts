import { useCallback, useEffect, useRef, useState } from 'react';

import type { MeasurementResponse } from '@entities/measurement';
import { getMeasurement, uploadVideo } from '@shared/api/measurements';

import {
  extractObjectKey,
  getPresigned,
  issueUserId,
  pollResult,
  putFile,
  requestFaceAnalysis,
  requestVoiceAnalysis,
  type FavResultData,
} from './favApi';
import { pickSentences } from './sentences';
import { blobToWavFile } from './wav';

export type DemoStatus = 'idle' | 'uploading' | 'processing' | 'done' | 'failed';

export interface DemoState {
  status: DemoStatus;
  progress: number;
  stage: string;
  result: MeasurementResponse | null;
  error: string | null;
}

const DEMO_IDLE: DemoState = {
  status: 'idle',
  progress: 0,
  stage: '',
  result: null,
  error: null,
};

export type FavPhase =
  | 'idle' // 시작 전
  | 'camera' // 카메라/마이크 켜짐, 시작 대기
  | 'countdown' // 3-2-1
  | 'reading' // 영상 녹화 + 문장별 음성 녹음
  | 'holding' // 문장은 다 읽었지만 영상 최소 길이(30초) 채우는 중
  | 'processing' // 업로드 + 분석 요청 + 결과 폴링
  | 'done'
  | 'error';

export const TOTAL_STEPS = 4;
const MIN_VIDEO_SEC = 30;
const CHAR_INTERVAL_MS = 140;
// 문장 하이라이트가 끝난 뒤(=다 읽을 시간이 지난 뒤) 자동으로 다음 문장으로
// 넘어가기까지의 여유 시간. 마지막 음절을 마저 읽을 시간을 준다.
const AUTO_ADVANCE_MS = 1800;

function pickVideoMime(): string {
  const candidates = ['video/webm;codecs=vp9', 'video/webm;codecs=vp8', 'video/webm', 'video/mp4'];
  for (const t of candidates) {
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported?.(t)) return t;
  }
  return '';
}

function pickAudioMime(): string {
  const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'];
  for (const t of candidates) {
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported?.(t)) return t;
  }
  return '';
}

/** recorder.stop()을 호출하고 onstop까지 기다린 뒤 모인 청크를 Blob으로 반환 */
function stopAndCollect(recorder: MediaRecorder, chunks: Blob[]): Promise<Blob> {
  return new Promise((resolve) => {
    const finish = () =>
      resolve(new Blob(chunks, { type: recorder.mimeType || 'application/octet-stream' }));
    if (recorder.state === 'inactive') {
      finish();
      return;
    }
    recorder.onstop = finish;
    recorder.stop();
  });
}

export function useFavMeasurement() {
  const [phase, setPhase] = useState<FavPhase>('idle');
  const [sentences, setSentences] = useState<string[]>([]);
  const [step, setStep] = useState(1); // 1~4
  const [charIndex, setCharIndex] = useState(0);
  const [readingDone, setReadingDone] = useState(false);
  const [countdown, setCountdown] = useState(3);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [stage, setStage] = useState(''); // processing 단계 표시
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FavResultData | null>(null);
  const [sessionId, setSessionId] = useState<string>('');
  const [demo, setDemo] = useState<DemoState>(DEMO_IDLE);
  const demoAbortRef = useRef(false);

  const rawStreamRef = useRef<MediaStream | null>(null);
  const videoRecorderRef = useRef<MediaRecorder | null>(null);
  const videoChunksRef = useRef<Blob[]>([]);
  const audioRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const wavFilesRef = useRef<File[]>([]);
  const highlightTimerRef = useRef<number | null>(null);
  const elapsedTimerRef = useRef<number | null>(null);
  const recordStartAtRef = useRef(0);
  const phaseRef = useRef<FavPhase>('idle');
  phaseRef.current = phase;

  const clearHighlight = useCallback(() => {
    if (highlightTimerRef.current !== null) {
      window.clearInterval(highlightTimerRef.current);
      highlightTimerRef.current = null;
    }
  }, []);

  const stopAll = useCallback(() => {
    demoAbortRef.current = true;
    clearHighlight();
    if (elapsedTimerRef.current !== null) {
      window.clearInterval(elapsedTimerRef.current);
      elapsedTimerRef.current = null;
    }
    try {
      if (audioRecorderRef.current?.state === 'recording') audioRecorderRef.current.stop();
      if (videoRecorderRef.current?.state === 'recording') videoRecorderRef.current.stop();
    } catch {
      // noop
    }
    rawStreamRef.current?.getTracks().forEach((t) => t.stop());
    rawStreamRef.current = null;
  }, [clearHighlight]);

  useEffect(() => stopAll, [stopAll]);

  /**
   * demo backend(rppg_toolbox) 분석 — mentai 체인과 병렬로, 같은 얼굴 영상을
   * 12개 rPPG 알고리즘에 태워 v1~v4 종합지수·consensus·전체 HRV를 받는다.
   * non-blocking: mentai 결과와 독립적으로 완료된다 (CPU/MPS라 더 느릴 수 있음).
   */
  const startDemoAnalysis = useCallback(async (videoBlob: Blob) => {
    demoAbortRef.current = false;
    setDemo({ status: 'uploading', progress: 0, stage: '영상 업로드 중…', result: null, error: null });
    try {
      const file = new File([videoBlob], 'fav-face.webm', { type: videoBlob.type || 'video/webm' });
      const { jobId } = await uploadVideo(file);
      for (;;) {
        if (demoAbortRef.current) return;
        await new Promise((r) => setTimeout(r, 1500));
        if (demoAbortRef.current) return;
        const r = await getMeasurement(jobId);
        const status: DemoStatus =
          r.status === 'done' ? 'done' : r.status === 'failed' ? 'failed' : 'processing';
        setDemo({
          status,
          progress: r.progress,
          stage: r.stage ?? '',
          result: r,
          error: r.status === 'failed' ? (r.error ?? '분석 실패') : null,
        });
        if (r.status === 'done' || r.status === 'failed') return;
      }
    } catch (e) {
      if (demoAbortRef.current) return;
      setDemo({ status: 'failed', progress: 0, stage: '', result: null, error: (e as Error).message });
    }
  }, []);

  /** 1. 카메라+마이크 권한 요청. 얼굴 추적 표시용으로 stream을 반환한다. */
  const enableCamera = useCallback(async (): Promise<MediaStream> => {
    setError(null);
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 30 } },
      audio: { sampleRate: 44100, channelCount: 1, echoCancellation: true, noiseSuppression: true },
    });
    rawStreamRef.current = stream;
    setPhase('camera');
    return stream;
  }, []);

  /** 문장 n의 오디오 녹음 + 글자 하이라이트 시작 */
  const beginStep = useCallback(
    (n: number, sentenceList: string[]) => {
      setStep(n);
      setCharIndex(0);
      setReadingDone(false);

      const audioTrack = rawStreamRef.current?.getAudioTracks()[0];
      if (!audioTrack) {
        setError('마이크 트랙을 찾을 수 없습니다');
        setPhase('error');
        return;
      }
      const mime = pickAudioMime();
      const recorder = new MediaRecorder(
        new MediaStream([audioTrack]),
        mime ? { mimeType: mime } : undefined,
      );
      audioChunksRef.current = [];
      recorder.ondataavailable = (ev) => {
        if (ev.data && ev.data.size > 0) audioChunksRef.current.push(ev.data);
      };
      recorder.start();
      audioRecorderRef.current = recorder;

      const text = sentenceList[n - 1].replace(/\|/g, '');
      clearHighlight();
      highlightTimerRef.current = window.setInterval(() => {
        setCharIndex((prev) => {
          if (prev >= text.length) {
            clearHighlight();
            setReadingDone(true);
            return prev;
          }
          return prev + 1;
        });
      }, CHAR_INTERVAL_MS);
    },
    [clearHighlight],
  );

  /** 영상 녹화 종료 → 업로드/분석/폴링 */
  const finishVideoAndProcess = useCallback(async () => {
    setPhase('processing');
    try {
      const videoRecorder = videoRecorderRef.current;
      if (!videoRecorder) throw new Error('영상 레코더가 없습니다');
      setStage('영상 마무리 중…');
      const videoBlob = await stopAndCollect(videoRecorder, videoChunksRef.current);
      rawStreamRef.current?.getTracks().forEach((t) => t.stop());
      rawStreamRef.current = null;

      // demo backend(rppg_toolbox)에도 같은 영상을 태운다 — 병렬, non-blocking.
      void startDemoAnalysis(videoBlob);

      // happywings와 동일: 컨테이너는 webm이어도 이름/타입은 mp4로 전송 (서버 검증 완료된 경로)
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const videoFile = new File([videoBlob], `face_${timestamp}.mp4`, { type: 'video/mp4' });
      const wavFiles = wavFilesRef.current;
      if (wavFiles.length !== TOTAL_STEPS) {
        throw new Error(`음성 파일이 ${wavFiles.length}개입니다 (4개 필요)`);
      }

      setStage('사용자 토큰 발급 중…');
      const userId = await issueUserId();
      const sid = crypto.randomUUID();
      setSessionId(sid);

      setStage('업로드 URL 발급 중…');
      const allFiles = [...wavFiles, videoFile];
      const presigned = await getPresigned(
        sid,
        userId,
        allFiles.map((f) => ({ name: f.name, mimeType: f.type })),
      );

      setStage('파일 업로드 중… (음성 4개 + 영상 1개)');
      await Promise.all(allFiles.map((f, i) => putFile(presigned[i].uploadURL, f)));

      const keys = presigned.map(extractObjectKey);
      const voiceKeys = keys.slice(0, TOTAL_STEPS);
      const videoKey = keys[TOTAL_STEPS];

      setStage('얼굴(rPPG) 분석 요청…');
      await requestFaceAnalysis(sid, userId, videoKey);

      setStage('음성 감정 분석 요청…');
      await requestVoiceAnalysis(sid, userId, voiceKeys);

      setStage('분석 결과 대기 중…');
      const data = await pollResult(sid, {
        onTick: (sec) => setStage(`분석 결과 대기 중… (${sec}초)`),
      });
      setResult(data);
      setPhase('done');
    } catch (e) {
      setError((e as Error).message || '처리 중 오류');
      setPhase('error');
    }
  }, [startDemoAnalysis]);

  /** "다음 문장" — 현재 문장의 오디오를 닫고 다음으로. 마지막이면 영상 최소길이 체크. */
  const nextSentence = useCallback(async () => {
    const recorder = audioRecorderRef.current;
    if (!recorder) return;
    clearHighlight();

    try {
      const blob = await stopAndCollect(recorder, audioChunksRef.current);
      const wav = await blobToWavFile(blob, `voice_recording_step_${step}.wav`);
      wavFilesRef.current.push(wav);
    } catch (e) {
      setError(`음성 변환 실패 (${step}번째): ${(e as Error).message}`);
      setPhase('error');
      return;
    }

    if (step < TOTAL_STEPS) {
      beginStep(step + 1, sentences);
      return;
    }

    // 4문장 완료 — 영상이 30초를 채웠으면 바로 종료, 아니면 holding
    const elapsed = (Date.now() - recordStartAtRef.current) / 1000;
    if (elapsed >= MIN_VIDEO_SEC) {
      void finishVideoAndProcess();
    } else {
      setPhase('holding');
    }
  }, [step, sentences, beginStep, clearHighlight, finishVideoAndProcess]);

  // 문장을 끝까지 읽으면(하이라이트 완료) 잠시 후 자동으로 다음 문장으로.
  // 사용자가 매번 버튼을 누를 필요 없이 4문장이 연속으로 진행된다.
  useEffect(() => {
    if (phase !== 'reading' || !readingDone) return;
    const id = window.setTimeout(() => {
      void nextSentence();
    }, AUTO_ADVANCE_MS);
    return () => window.clearTimeout(id);
  }, [phase, readingDone, nextSentence]);

  // holding 중 30초 도달하면 자동 종료
  useEffect(() => {
    if (phase !== 'holding') return;
    const id = window.setInterval(() => {
      const elapsed = (Date.now() - recordStartAtRef.current) / 1000;
      if (elapsed >= MIN_VIDEO_SEC) {
        window.clearInterval(id);
        void finishVideoAndProcess();
      }
    }, 250);
    return () => window.clearInterval(id);
  }, [phase, finishVideoAndProcess]);

  /** 2. 측정 시작 (카운트다운 → 영상 녹화 + 1번 문장) */
  const start = useCallback(() => {
    if (!rawStreamRef.current) {
      setError('카메라가 켜져 있지 않습니다');
      return;
    }
    const picked = pickSentences();
    setSentences(picked);
    wavFilesRef.current = [];
    setResult(null);
    setError(null);
    setPhase('countdown');
    setCountdown(3);

    let n = 3;
    const id = window.setInterval(() => {
      n -= 1;
      if (n > 0) {
        setCountdown(n);
        return;
      }
      window.clearInterval(id);

      // 영상 녹화 시작 (원본 비디오 트랙 — 서버가 자체적으로 얼굴 ROI 추출)
      const videoTrack = rawStreamRef.current?.getVideoTracks()[0];
      if (!videoTrack) {
        setError('카메라 트랙을 찾을 수 없습니다');
        setPhase('error');
        return;
      }
      const mime = pickVideoMime();
      const recorder = new MediaRecorder(new MediaStream([videoTrack]), {
        ...(mime ? { mimeType: mime } : {}),
        videoBitsPerSecond: 5_000_000,
      });
      videoChunksRef.current = [];
      recorder.ondataavailable = (ev) => {
        if (ev.data && ev.data.size > 0) videoChunksRef.current.push(ev.data);
      };
      recorder.start(1000);
      videoRecorderRef.current = recorder;
      recordStartAtRef.current = Date.now();
      setElapsedSec(0);
      elapsedTimerRef.current = window.setInterval(() => {
        setElapsedSec(Math.floor((Date.now() - recordStartAtRef.current) / 1000));
      }, 500);

      setPhase('reading');
      beginStep(1, picked);
    }, 1000);
  }, [beginStep]);

  /** 처음부터 다시 */
  const reset = useCallback(() => {
    stopAll();
    wavFilesRef.current = [];
    videoChunksRef.current = [];
    audioChunksRef.current = [];
    setPhase('idle');
    setStep(1);
    setCharIndex(0);
    setReadingDone(false);
    setElapsedSec(0);
    setStage('');
    setError(null);
    setResult(null);
    setSessionId('');
    setDemo(DEMO_IDLE);
  }, [stopAll]);

  return {
    phase,
    sentences,
    step,
    charIndex,
    readingDone,
    countdown,
    elapsedSec,
    minVideoSec: MIN_VIDEO_SEC,
    stage,
    error,
    result,
    sessionId,
    demo,
    enableCamera,
    start,
    nextSentence,
    reset,
  };
}
