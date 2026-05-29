import { useEffect, useState } from 'react';

import { uploadVideo } from '@shared/api/measurements';
import { useMeasurementStore } from '@features/run-measurement/model/measurementStore';

import { useRecord } from '../model/useRecord';

const DURATIONS = [15, 30, 45, 60] as const;

export function RecordPanel() {
  const setJobId = useMeasurementStore((s) => s.setJobId);
  const [seconds, setSeconds] = useState<number>(30);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleComplete = async (file: File) => {
    setUploadError(null);
    setUploading(true);
    try {
      const { jobId } = await uploadVideo(file);
      setJobId(jobId);
    } catch (e) {
      setUploadError((e as Error).message || 'upload failed');
    } finally {
      setUploading(false);
    }
  };

  const { status, error, remainingMs, attachVideo, requestStream, start, stop, stopCamera } =
    useRecord({ onComplete: handleComplete });

  useEffect(() => {
    return () => stopCamera();
  }, [stopCamera]);

  const cameraOn = status === 'preview' || status === 'recording' || status === 'finalizing';
  const isRecording = status === 'recording';

  return (
    <section className="rounded-2xl border bg-white p-5 shadow-sm flex flex-col gap-4">
      <header className="flex items-baseline justify-between">
        <div>
          <h2 className="text-base font-semibold">웹캠으로 직접 측정</h2>
          <p className="text-xs text-neutral-500 mt-0.5">
            정면 / 균일 조명 / 움직임 최소화. 녹화 후 자동으로 분석이 시작됩니다.
          </p>
        </div>
        {cameraOn && (
          <button
            onClick={stopCamera}
            className="text-xs text-neutral-500 hover:text-rose-600 underline"
          >
            카메라 끄기
          </button>
        )}
      </header>

      <div className="relative bg-neutral-900 rounded-xl overflow-hidden aspect-video">
        <video
          ref={attachVideo}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover transform -scale-x-100"
        />
        {!cameraOn && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-neutral-400 gap-3">
            <CameraIcon />
            <p className="text-sm">카메라가 꺼져 있습니다</p>
            <button
              onClick={requestStream}
              disabled={status === 'requesting'}
              className="px-4 py-2 bg-sky-500 text-white rounded-full text-sm font-medium hover:bg-sky-600 disabled:opacity-60"
            >
              {status === 'requesting' ? '권한 요청 중…' : '카메라 켜기'}
            </button>
          </div>
        )}
        {isRecording && (
          <>
            <div className="absolute top-3 left-3 bg-rose-600 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1.5">
              <span className="block w-2 h-2 bg-white rounded-full animate-pulse" /> REC
            </div>
            <div className="absolute top-3 right-3 bg-black/60 text-white text-xs px-2 py-1 rounded">
              남은 시간 {Math.ceil(remainingMs / 1000)}s
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/20">
              <div
                className="h-full bg-rose-500 transition-all"
                style={{ width: `${100 - (remainingMs / (seconds * 1000)) * 100}%` }}
              />
            </div>
          </>
        )}
        {uploading && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center text-white text-sm">
            업로드 중…
          </div>
        )}
      </div>

      {cameraOn && !isRecording && !uploading && (
        <div className="flex flex-wrap items-center gap-3">
          <div className="inline-flex rounded-full border bg-neutral-50 p-1">
            {DURATIONS.map((d) => (
              <button
                key={d}
                onClick={() => setSeconds(d)}
                className={`text-sm px-3 py-1 rounded-full transition-colors ${
                  seconds === d
                    ? 'bg-sky-500 text-white shadow-sm'
                    : 'text-neutral-600 hover:text-neutral-900'
                }`}
              >
                {d}s
              </button>
            ))}
          </div>
          <button
            onClick={() => start(seconds)}
            className="ml-auto px-5 py-2 bg-rose-500 text-white rounded-full text-sm font-semibold hover:bg-rose-600"
          >
            {seconds}초 녹화 시작
          </button>
        </div>
      )}

      {isRecording && (
        <div className="flex justify-end">
          <button
            onClick={stop}
            className="px-4 py-2 border border-rose-300 text-rose-700 rounded-full text-sm hover:bg-rose-50"
          >
            지금 중지
          </button>
        </div>
      )}

      {(error || uploadError) && (
        <p className="text-sm text-rose-600">{error ?? uploadError}</p>
      )}

      <p className="text-[11px] text-neutral-400 leading-relaxed">
        ⚠ 녹화된 영상은 분석 후 서버에서 즉시 삭제됩니다. 의료기기가 아닙니다.
      </p>
    </section>
  );
}

function CameraIcon() {
  return (
    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M3 7h3l2-2h8l2 2h3v12H3V7z" />
      <circle cx="12" cy="13" r="4" />
    </svg>
  );
}
