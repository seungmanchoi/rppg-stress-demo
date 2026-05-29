import { useCallback, useEffect, useRef, useState } from 'react';

export type RecordStatus =
  | 'idle'
  | 'requesting'
  | 'preview'
  | 'recording'
  | 'finalizing'
  | 'error';

interface UseRecordOptions {
  onComplete: (file: File) => void;
}

/**
 * Webcam capture + MediaRecorder pipeline.
 *
 * Lifecycle:
 *   idle → requestStream() → preview (camera live, mic muted)
 *   start(seconds) → recording → auto-stop after `seconds` → finalizing
 *     → callback with File(.webm) → preview (stream stays open)
 */
export function useRecord({ onComplete }: UseRecordOptions) {
  const [status, setStatus] = useState<RecordStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [remainingMs, setRemainingMs] = useState(0);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const stopTimerRef = useRef<number | null>(null);
  const tickTimerRef = useRef<number | null>(null);

  const attachVideo = useCallback((el: HTMLVideoElement | null) => {
    videoRef.current = el;
    if (el && streamRef.current) {
      el.srcObject = streamRef.current;
    }
  }, []);

  const cleanupTimers = useCallback(() => {
    if (stopTimerRef.current !== null) {
      window.clearTimeout(stopTimerRef.current);
      stopTimerRef.current = null;
    }
    if (tickTimerRef.current !== null) {
      window.clearInterval(tickTimerRef.current);
      tickTimerRef.current = null;
    }
  }, []);

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }, []);

  const requestStream = useCallback(async () => {
    setError(null);
    setStatus('requesting');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 30 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      setStatus('preview');
    } catch (e) {
      setError((e as Error).message || 'camera access denied');
      setStatus('error');
    }
  }, []);

  const pickMimeType = useCallback(() => {
    const candidates = [
      'video/webm;codecs=vp9',
      'video/webm;codecs=vp8',
      'video/webm',
      'video/mp4',
    ];
    for (const t of candidates) {
      if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported?.(t)) return t;
    }
    return '';
  }, []);

  const start = useCallback(
    (seconds: number) => {
      if (!streamRef.current) {
        setError('no camera stream — click camera button first');
        setStatus('error');
        return;
      }
      const mimeType = pickMimeType();
      chunksRef.current = [];
      let recorder: MediaRecorder;
      try {
        recorder = new MediaRecorder(streamRef.current, mimeType ? { mimeType } : undefined);
      } catch (e) {
        setError((e as Error).message || 'MediaRecorder init failed');
        setStatus('error');
        return;
      }
      recorderRef.current = recorder;

      recorder.ondataavailable = (ev) => {
        if (ev.data && ev.data.size > 0) chunksRef.current.push(ev.data);
      };
      recorder.onstop = () => {
        cleanupTimers();
        setRemainingMs(0);
        const type = recorder.mimeType || mimeType || 'video/webm';
        const ext = type.includes('mp4') ? 'mp4' : 'webm';
        const blob = new Blob(chunksRef.current, { type });
        const file = new File([blob], `webcam-${Date.now()}.${ext}`, { type });
        chunksRef.current = [];
        setStatus('finalizing');
        try {
          onComplete(file);
        } finally {
          setStatus('preview');
        }
      };
      recorder.start();
      setStatus('recording');
      const durationMs = Math.max(1000, seconds * 1000);
      setRemainingMs(durationMs);
      const startedAt = Date.now();
      tickTimerRef.current = window.setInterval(() => {
        const left = Math.max(0, durationMs - (Date.now() - startedAt));
        setRemainingMs(left);
      }, 100);
      stopTimerRef.current = window.setTimeout(() => {
        if (recorder.state === 'recording') recorder.stop();
      }, durationMs);
    },
    [pickMimeType, cleanupTimers, onComplete],
  );

  const stop = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state === 'recording') {
      recorderRef.current.stop();
    }
  }, []);

  useEffect(() => {
    return () => {
      cleanupTimers();
      try {
        recorderRef.current?.state === 'recording' && recorderRef.current.stop();
      } catch {
        // noop
      }
      stopStream();
    };
  }, [cleanupTimers, stopStream]);

  return {
    status,
    error,
    remainingMs,
    attachVideo,
    requestStream,
    start,
    stop,
    stopCamera: stopStream,
  };
}
