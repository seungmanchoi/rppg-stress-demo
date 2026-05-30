import { FaceDetector, FilesetResolver } from '@mediapipe/tasks-vision';
import { useCallback, useEffect, useRef, useState } from 'react';

const WASM_BASE = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm';
const MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite';

const OUTPUT_SIZE = 480;
const PADDING = 2.4;

// One Euro Filter: lower minCutoff = smoother at rest; lower beta = less reactive.
const POS_MIN_CUTOFF = 0.35;
const POS_BETA = 0.006;
const SIZE_MIN_CUTOFF = 0.18;
const SIZE_BETA = 0.002;
const D_CUTOFF = 1.0;

class OneEuro {
  private x: number | null = null;
  private dx = 0;
  private t: number | null = null;
  private minCutoff: number;
  private beta: number;
  private dCutoff: number;
  constructor(minCutoff: number, beta: number, dCutoff: number) {
    this.minCutoff = minCutoff;
    this.beta = beta;
    this.dCutoff = dCutoff;
  }
  private alpha(cutoff: number, dt: number) {
    const tau = 1 / (2 * Math.PI * cutoff);
    return 1 / (1 + tau / dt);
  }
  filter(value: number, tMs: number): number {
    if (this.x === null || this.t === null) {
      this.x = value;
      this.t = tMs;
      return value;
    }
    const dt = Math.max(1 / 120, (tMs - this.t) / 1000);
    const dxRaw = (value - this.x) / dt;
    this.dx = this.dx + this.alpha(this.dCutoff, dt) * (dxRaw - this.dx);
    const cutoff = this.minCutoff + this.beta * Math.abs(this.dx);
    this.x = this.x + this.alpha(cutoff, dt) * (value - this.x);
    this.t = tMs;
    return this.x;
  }
  reset() {
    this.x = null;
    this.dx = 0;
    this.t = null;
  }
}

type Box = { x: number; y: number; w: number; h: number };

let detectorPromise: Promise<FaceDetector> | null = null;
function loadDetector(): Promise<FaceDetector> {
  if (!detectorPromise) {
    detectorPromise = (async () => {
      const filesetResolver = await FilesetResolver.forVisionTasks(WASM_BASE);
      return FaceDetector.createFromOptions(filesetResolver, {
        baseOptions: { modelAssetPath: MODEL_URL, delegate: 'GPU' },
        runningMode: 'VIDEO',
        minDetectionConfidence: 0.5,
      });
    })().catch((e) => {
      detectorPromise = null;
      throw e;
    });
  }
  return detectorPromise;
}

interface UseFaceTrackerResult {
  attachVideo: (el: HTMLVideoElement | null) => void;
  attachCanvas: (el: HTMLCanvasElement | null) => void;
  start: (stream: MediaStream) => Promise<void>;
  stop: () => void;
  faceDetected: boolean;
  loading: boolean;
  error: string | null;
  getCanvasStream: () => MediaStream | null;
}

export function useFaceTracker(): UseFaceTrackerResult {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const detectorRef = useRef<FaceDetector | null>(null);
  const rafRef = useRef<number | null>(null);
  const lastBoxRef = useRef<Box | null>(null);
  const canvasStreamRef = useRef<MediaStream | null>(null);
  const filtersRef = useRef({
    x: new OneEuro(POS_MIN_CUTOFF, POS_BETA, D_CUTOFF),
    y: new OneEuro(POS_MIN_CUTOFF, POS_BETA, D_CUTOFF),
    w: new OneEuro(SIZE_MIN_CUTOFF, SIZE_BETA, D_CUTOFF),
    h: new OneEuro(SIZE_MIN_CUTOFF, SIZE_BETA, D_CUTOFF),
  });

  const [faceDetected, setFaceDetected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const attachVideo = useCallback((el: HTMLVideoElement | null) => {
    videoRef.current = el;
  }, []);
  const attachCanvas = useCallback((el: HTMLCanvasElement | null) => {
    canvasRef.current = el;
    if (el) {
      el.width = OUTPUT_SIZE;
      el.height = OUTPUT_SIZE;
    }
  }, []);

  const stop = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    canvasStreamRef.current?.getTracks().forEach((t) => t.stop());
    canvasStreamRef.current = null;
    lastBoxRef.current = null;
    filtersRef.current.x.reset();
    filtersRef.current.y.reset();
    filtersRef.current.w.reset();
    filtersRef.current.h.reset();
    setFaceDetected(false);
  }, []);

  const start = useCallback(
    async (stream: MediaStream) => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas) return;
      video.srcObject = stream;
      await video.play().catch(() => undefined);

      setLoading(true);
      setError(null);
      try {
        detectorRef.current = await loadDetector();
      } catch (e) {
        setError((e as Error).message || 'face detector load failed');
        setLoading(false);
        return;
      }
      setLoading(false);

      const ctx = canvas.getContext('2d', { willReadFrequently: false });
      if (!ctx) return;

      const DETECTOR_INTERVAL_MS = 60;
      let lastDetectAt = 0;
      const tick = () => {
        const v = videoRef.current;
        const c = canvasRef.current;
        const detector = detectorRef.current;
        if (!v || !c || !detector || v.readyState < 2) {
          rafRef.current = requestAnimationFrame(tick);
          return;
        }
        const vw = v.videoWidth || 640;
        const vh = v.videoHeight || 480;

        let detection: Box | null = null;
        const now = performance.now();
        if (now - lastDetectAt >= DETECTOR_INTERVAL_MS) {
          lastDetectAt = now;
          try {
            const result = detector.detectForVideo(v, now);
            const top = result.detections?.[0];
            if (top?.boundingBox) {
              const bb = top.boundingBox;
              detection = {
                x: bb.originX,
                y: bb.originY,
                w: bb.width,
                h: bb.height,
              };
            }
          } catch {
            // detector hiccup — keep last box
          }
        }

        if (detection) {
          const now = performance.now();
          const f = filtersRef.current;
          lastBoxRef.current = {
            x: f.x.filter(detection.x, now),
            y: f.y.filter(detection.y, now),
            w: f.w.filter(detection.w, now),
            h: f.h.filter(detection.h, now),
          };
          setFaceDetected(true);
        } else if (!lastBoxRef.current) {
          setFaceDetected(false);
        }

        const box = lastBoxRef.current;
        ctx.fillStyle = '#0a0a0a';
        ctx.fillRect(0, 0, c.width, c.height);

        if (box) {
          const side = Math.max(box.w, box.h) * PADDING;
          const cx = box.x + box.w / 2;
          const cy = box.y + box.h / 2;
          let sx = cx - side / 2;
          let sy = cy - side / 2;
          let sSide = side;
          sx = Math.max(0, Math.min(vw - 1, sx));
          sy = Math.max(0, Math.min(vh - 1, sy));
          sSide = Math.min(sSide, vw - sx, vh - sy);
          if (sSide > 0) {
            ctx.drawImage(v, sx, sy, sSide, sSide, 0, 0, c.width, c.height);
          }
        } else {
          ctx.fillStyle = '#9ca3af';
          ctx.font = '16px system-ui';
          ctx.textAlign = 'center';
          ctx.fillText('얼굴을 화면 안에 두세요', c.width / 2, c.height / 2);
        }

        rafRef.current = requestAnimationFrame(tick);
      };
      rafRef.current = requestAnimationFrame(tick);
    },
    [],
  );

  const getCanvasStream = useCallback((): MediaStream | null => {
    const c = canvasRef.current;
    if (!c) return null;
    if (!canvasStreamRef.current) {
      canvasStreamRef.current = c.captureStream(30);
    }
    return canvasStreamRef.current;
  }, []);

  useEffect(() => stop, [stop]);

  return { attachVideo, attachCanvas, start, stop, faceDetected, loading, error, getCanvasStream };
}
