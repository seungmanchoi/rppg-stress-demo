# rPPG Stress Demo — Design Spec

- **작성일**: 2026-05-29
- **상태**: 승인 대기 → 구현 계획 작성 단계
- **저자**: Seungman Choi (smchoi@clify.co.kr)
- **목표**: rPPG-Toolbox(https://github.com/ubicomplab/rPPG-Toolbox)를 백엔드로 사용하여 얼굴 영상에서 심혈관/자율신경 지표 및 스트레스 지수를 추출하고, 8개 알고리즘의 결과를 동시에 한 화면에서 비교/검증하는 웹 데모를 구축한다.

---

## 1. 문제 정의 & 성공 기준

### 1.1 문제
- 사용자가 본인 얼굴 영상을 업로드하면, 비접촉 원격 PPG로 심박/HRV/스트레스 지수가 산출되어야 한다.
- 단일 모델의 결과는 신뢰하기 어려우므로 여러 알고리즘 결과를 동시에 보여주고 **신뢰도(reliability)** 를 함께 표시해야 한다.
- 의료기기가 아닌 교육/연구 데모임을 명시.

### 1.2 성공 기준
- 30초 영상 업로드 후 30초 이내에 8개 알고리즘 모두 결과 표시 (Apple M4 Pro 기준).
- UBFC-rPPG 공개 데이터 1개 샘플에 대해 contact PPG ground truth와 평균 HR MAE ≤ 3 BPM.
- 각 알고리즘 카드에 "어떤 데이터인지" 한 줄 설명 + 신뢰도 등급 표시.
- 안정 baseline 영상과 스트레스 유발(Stroop/암산) 영상 비교 시 composite stress score 평균 +10 이상 차이 관찰.

### 1.3 비목표 (YAGNI)
- 다중 사용자/계정 관리, 인증, DB 영속화.
- 실시간 웹캠 스트리밍 (1차 범위 외).
- 의료 진단/임상 검증.

---

## 2. 기술 스택

| 영역 | 선택 | 이유 |
|------|------|------|
| Backend | FastAPI + Python 3.11 | rPPG-Toolbox 통합, async 지원 |
| Backend 패키지 관리 | uv | 빠른 의존성 해결 |
| ML 런타임 | PyTorch + MPS | Apple Silicon 가속 |
| 얼굴 검출 | MediaPipe FaceMesh | ROI 추출 안정성 |
| Frontend | React 18 + Vite + TypeScript | 빠른 개발, 타입 안전성 |
| 아키텍처 | Feature-Sliced Design | 영역별 분리, 유지보수성 |
| 상태 관리 | TanStack Query + Zustand | 서버 상태/UI 상태 분리 |
| UI | Tailwind + shadcn/ui + Recharts | 디자인 시스템 + 차트 |

---

## 3. 시스템 아키텍처

```
┌─────────────────────────────────────────────┐         ┌──────────────────────────────────────┐
│        Frontend (React + Vite + TS, FSD)    │         │   Backend (FastAPI + rPPG-Toolbox)    │
│                                             │  POST   │                                       │
│  pages/measure                              │ ──────▶ │  /api/v1/measurements                 │
│  widgets/consensus-dashboard                │         │  /api/v1/measurements/{id}            │
│  widgets/algorithm-cards-grid (8 cards)     │ ◀──────  │  /api/v1/measurements/{id}/stream    │
│  features/upload-video, run-measurement     │  SSE    │                                       │
│  entities/measurement, algorithm            │         │  Pipeline:                            │
│  shared/api, shared/ui, shared/lib          │         │   Face/ROI → 8x algo parallel         │
└─────────────────────────────────────────────┘         │   → BVP → IBI → HRV → Stress          │
                                                        │   → Reliability + Consensus           │
                                                        └──────────────────────────────────────┘
```

### 3.1 처리 흐름

```
[1] User uploads mp4 (10~120s)
[2] FastAPI saves /tmp/measurements/{job_id}.mp4 → returns job_id (202)
[3] Pipeline worker:
    a) Decode frames (OpenCV @ 30fps)
    b) Face detect via MediaPipe FaceMesh → forehead + cheeks ROI
    c) Compute mean RGB per frame → T×3 signal
    d) Quality gate: detected ratio, motion magnitude, brightness
    e) Run 8 algorithms in parallel (ProcessPool for unsup, asyncio MPS queue for deep)
    f) Per algo: BVP → IBI → HRV → Stress + Reliability
    g) Reliability-weighted consensus
[4] Frontend renders consensus dashboard + 8 cards
```

---

## 4. 알고리즘 구성 (8개)

| ID | 종류 | Backbone | Pretrain | Weight | 핵심 출력 | 한 줄 설명 |
|----|------|----------|----------|--------|----------|----------|
| POS | Unsup | Signal processing | — | 0 MB | BVP, HR | RGB → 피부 톤 직교 평면 투영으로 혈류 분리 (de Haan 2014) |
| CHROM | Unsup | Signal processing | — | 0 MB | BVP, HR | 피부 톤 표준화 후 색 차이 신호화 (de Haan 2013) |
| OMIT | Unsup | Signal processing | — | 0 MB | BVP, HR | Orthogonal Matrix Image Transformation, 조명 강건 |
| TS-CAN | Supervised | 2D-CNN + Temporal Shift | UBFC-rPPG | ~30 MB | BVP, HR | 모바일 친화 실시간 모델 |
| EfficientPhys | Supervised | 경량 CNN | UBFC-rPPG | ~25 MB | BVP, HR | 가장 빠른 deep 모델 |
| PhysFormer | Supervised | Video Transformer | PURE | ~200 MB | BVP, HR | Transformer 기반 SOTA |
| RhythmFormer | Supervised | Freq-attention | PURE | ~180 MB | BVP, HR | 주파수 영역 attention, HRV 안정 |
| BigSmall | Supervised | Multitask CNN | BP4D | ~80 MB | BVP, HR, **호흡수, AU** | 멀티태스크 (호흡수 보너스) |

총 가중치 약 **520MB**, 첫 실행 시 자동 다운로드.

---

## 5. 데이터 모델

### 5.1 TypeScript / Pydantic v2 (동형)

```ts
type AlgorithmId =
  | 'POS' | 'CHROM' | 'OMIT'
  | 'TS-CAN' | 'EfficientPhys' | 'PhysFormer' | 'RhythmFormer' | 'BigSmall';

interface AlgorithmMeta {
  id: AlgorithmId;
  displayName: string;
  shortDescription: string;
  type: 'unsupervised' | 'supervised';
  backbone: string;
  pretrainedOn?: string;
  modelSizeMB?: number;
}

interface HRVMetrics {
  hrBpm: number;
  ibiMeanMs: number;
  sdnnMs: number;
  rmssdMs: number;
  pnn50Pct: number;
  lfPower: number;
  hfPower: number;
  lfHfRatio: number;
  sd1: number;
  sd2: number;
}

interface StressIndices {
  baevskySi: number;            // 50~1500
  baevskyLevel: 'normal' | 'mild' | 'moderate' | 'high';
  lfHfStress: number;           // 0~100
  compositeScore: number;       // 0~100  (카드 메인 수치)
  compositeLevel: 'low' | 'mid' | 'high' | 'very_high';
}

interface Reliability {
  score: number;                // 0~100
  grade: 'low' | 'medium' | 'high';
  components: {
    snrDb: number;
    faceTrackingPct: number;
    deviationFromConsensus: number;
    motionPenalty: number;
  };
}

interface AlgorithmResult {
  meta: AlgorithmMeta;
  hrv: HRVMetrics;
  stress: StressIndices;
  reliability: Reliability;
  bvpSparkline: number[];       // 100~200 다운샘플 포인트
  extras?: { respirationRpm?: number };  // BigSmall만
  computeMs: number;
}

interface ConsensusResult {
  stressScore: number;          // reliability-weighted median
  stressLevel: 'low' | 'mid' | 'high' | 'very_high';
  hrBpm: number;
  rmssdMs: number;
  lfHfRatio: number;
  baevskySi: number;
  reliability: Reliability;
  contributingAlgorithms: number;
}

interface MeasurementResponse {
  jobId: string;
  status: 'queued' | 'processing' | 'done' | 'failed';
  progress: number;
  videoMeta: { durationS: number; fps: number; resolution: [number, number] };
  consensus?: ConsensusResult;
  algorithms?: AlgorithmResult[];   // 길이 8
  warnings?: string[];
  disclaimer: string;
}
```

---

## 6. API

```
POST   /api/v1/measurements
       multipart: video (mp4|webm|mov, ≤ 200MB, 10~120s)
       ?algorithms=POS,CHROM,...   (default: 모든 8개)
       → 202 { jobId, status: "queued" }

GET    /api/v1/measurements/{jobId}
       → 200 MeasurementResponse

GET    /api/v1/measurements/{jobId}/stream
       SSE: { progress, stage, partialAlgorithms? }

DELETE /api/v1/measurements/{jobId}
       임시 파일 삭제

GET    /api/v1/algorithms
       → AlgorithmMeta[]

GET    /api/v1/health
       → { status, mpsAvailable, weightsLoaded: AlgorithmId[] }
```

정책:
- CORS: dev `http://localhost:5173`
- 동시 작업 1개 제한 (단일 사용자 데모)
- 결과는 1시간 TTL, 영상 파일은 처리 직후 삭제

---

## 7. 신뢰도 / 스트레스 산출 공식

### 7.1 IBI 추출
```
BVP → 0.7~3.5 Hz Butterworth bandpass →
scipy.find_peaks(min_distance=0.4s) →
IBI series (ms) → median ± 3·MAD outlier removal
```

### 7.2 HRV
```
SDNN  = std(IBI)
RMSSD = sqrt(mean(diff(IBI)²))
pNN50 = count(|diff(IBI)| > 50) / N

PSD via Lomb-Scargle on (t_i, IBI_i)
LF = ∫ PSD over [0.04, 0.15] Hz
HF = ∫ PSD over [0.15, 0.40] Hz
LF/HF = LF / HF
SD1, SD2 = Poincaré plot
```

### 7.3 Baevsky Stress Index
```
50ms bin IBI histogram → Mo (mode IBI, seconds)
AMo  = mode bin count / N · 100   (%)
MxDMn = (max - min)(IBI in seconds)
SI = AMo / (2 · Mo · MxDMn)
```
구간: 50–150 normal / 150–500 mild / 500–900 moderate / >900 high

### 7.4 Composite Stress Score (카드 메인)
```
s_baevsky = clip(log10(SI/50) / log10(1500/50), 0, 1)
s_lfhf    = clip((LF/HF - 0.5) / 4.0, 0, 1)
s_rmssd   = clip(1 - RMSSD/60, 0, 1)
compositeScore = 100 · (0.4·s_baevsky + 0.4·s_lfhf + 0.2·s_rmssd)
```
구간: 0–30 low / 30–60 mid / 60–80 high / 80–100 very_high

### 7.5 Reliability (카드)
```
snr_score       = clip((SNR_dB + 5) / 15, 0, 1)
tracking_score  = face_detected_frames / total_frames
motion_penalty  = clip(1 - mean_optical_flow / 5px, 0, 1)
consensus_score = clip(1 - |HR - median_HR| / 10, 0, 1)

reliability = 100 · (0.30·snr_score + 0.25·tracking_score
                   + 0.20·motion_penalty + 0.25·consensus_score)
```
등급: ≥75 high / 45–75 medium / <45 low

### 7.6 Consensus (대시보드)
```
weights_i = max(reliability_i - 30, 0)
consensus_HR    = weighted_median(HR_i, weights_i)
consensus_RMSSD = weighted_median(RMSSD_i, weights_i)
consensus_Stress = weighted_median(compositeScore_i, weights_i)
consensus_reliability = (eligible_ratio) · weighted_mean(reliability_i, weights_i)
```

---

## 8. 디렉토리 구조

### 8.1 Frontend (FSD)
```
frontend/src/
├─ app/                         providers, styles, App.tsx
├─ pages/measure                MeasurePage.tsx
├─ pages/about                  AboutPage.tsx
├─ widgets/consensus-dashboard
├─ widgets/algorithm-cards-grid
├─ widgets/measurement-progress
├─ features/upload-video
├─ features/run-measurement
├─ features/algorithm-result-card
├─ entities/measurement
├─ entities/algorithm
└─ shared/{api,ui,lib,config}
```

### 8.2 Backend
```
backend/app/
├─ main.py
├─ api/v1/{measurements,algorithms,health}.py
├─ core/{config,jobs,events}.py
├─ schemas/{measurement,algorithm}.py
├─ pipeline/
│  ├─ orchestrator.py
│  ├─ preprocess/{face_roi,frame_decoder,quality_gate}.py
│  ├─ algorithms/{base,unsupervised,supervised}/
│  ├─ hrv/{peak_detect,time_domain,freq_domain,nonlinear}.py
│  ├─ stress/{baevsky,composite}.py
│  └─ reliability/{snr,tracking,scoring}.py
├─ models/registry.py
└─ utils/weights_downloader.py
backend/rppg_toolbox/   (vendor or submodule)
backend/weights/        (.gitignore)
backend/tests/          (pytest)
backend/scripts/        (download_weights, benchmark)
```

---

## 9. UI 와이어프레임

- 상단: **Consensus Dashboard** — 통합 스트레스 게이지(0~100), HR/RMSSD/LF-HF/Baevsky, 신뢰도 등급, 기여 알고리즘 수
- 하단: **4×2 카드 그리드** — reliability 내림차순 정렬, 각 카드에 이름·1줄 설명·학습데이터셋·신뢰도 뱃지·HR/RMSSD/LF-HF/Baev/Stress·BVP 스파크라인
- 카드 클릭 시 expand: 전체 HRV 메트릭, 전체 BVP waveform, 신뢰도 breakdown, paper 링크
- 하단 푸터: "Not a medical device" 고지

---

## 10. 에러 / 엣지케이스

| 상황 | 처리 |
|------|------|
| 영상 < 10s | 업로드 거부 |
| 영상 > 120s | 거부 |
| 얼굴 미검출 비율 > 30% | warning 추가 + reliability 자동 하락 |
| 모든 알고리즘 reliability < 45 | consensus 미산출, 재촬영 모달 |
| MPS 미지원/실패 | CPU fallback (`PYTORCH_ENABLE_MPS_FALLBACK=1`) |
| 가중치 미존재 | 시작 시 자동 다운로드, 실패 시 해당 알고리즘 disabled (회색 카드) |
| 코덱 미지원 | ffmpeg로 재인코딩 |

---

## 11. 테스트 전략

| 레이어 | 도구 | 케이스 |
|--------|------|--------|
| HRV 단위 | pytest | 합성 IBI → RMSSD/LF/HF ±5% |
| 알고리즘 어댑터 | pytest | 합성 RGB → HR ±2 BPM |
| Pipeline | pytest | 30s sample → 8개 결과 |
| API | httpx | upload → poll → done flow |
| Frontend 단위 | Vitest | selector, formatter |
| E2E | Playwright | 업로드 → 진행률 → 8장 렌더 |
| 회귀 | UBFC-rPPG subject1 → 골든 JSON diff |

---

## 12. 실행

```bash
# Backend
cd backend && uv sync
PYTORCH_ENABLE_MPS_FALLBACK=1 uv run uvicorn app.main:app --reload --port 8000
uv run python scripts/download_weights.py     # 최초 1회 ~520MB

# Frontend
cd frontend && pnpm install && pnpm dev       # http://localhost:5173
```

### 의존성
- backend: fastapi, uvicorn[standard], pydantic v2, torch (MPS), opencv-python, mediapipe, scipy, numpy, sse-starlette
- frontend: react@18, vite, typescript, @tanstack/react-query, zustand, tailwindcss, recharts, react-dropzone, shadcn/ui

---

## 13. Disclaimer

본 데모는 의료기기가 아니며 진단/치료 목적으로 사용할 수 없다. 모든 결과는 교육/연구용 추정치이며, 임상적 판단에 사용해서는 안 된다. UI 푸터에 항상 명시한다.
