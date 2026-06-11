# rPPG Stress Demo

웹캠 얼굴 영상으로 **심박(HR) · 심박변이도(HRV) · 스트레스 지수**를 비접촉으로 추정하는 데모.
12개 rPPG 알고리즘을 동시에 실행하고, 결과를 신뢰도 기반으로 합의하여 0~100 스트레스 점수를 산출합니다.

> ⚠ **의료기기가 아닙니다.** 교육·연구용 추정치이며 진단·치료에 사용할 수 없습니다.

---

## 핵심 기능

- 🎥 **브라우저에서 직접 녹화** — getUserMedia + MediaRecorder, 15/30/45/60초 선택
- 👤 **실시간 얼굴 추적·크롭** — MediaPipe FaceDetector + One Euro Filter로 떨림 없이 얼굴만 화면 중앙에 고정
- 🧠 **12개 알고리즘 동시 실행** — 비지도 5종(POS·CHROM·OMIT·GREEN·ICA) + 지도 7종(TS-CAN·EfficientPhys·PhysFormer·RhythmFormer·BigSmall·PhysNet·DeepPhys)
- 📊 **HRV 풀세트 추출** — HR, SDNN, RMSSD, pNN50, LF/HF, Poincaré SD1/SD2, Baevsky SI
- 🛡 **신뢰도 가중 합의** — 각 알고리즘 결과에 SNR·트래킹·움직임·합의편차 기반 0~100 신뢰도 부여, 신뢰도 30 미만 카드는 합의에서 제외
- ⚙ **harmonic 자동 보정** — supervised 모델이 2배 주파수(예: 167 BPM)에 락되면 자동으로 절반 보정
- 🚥 **이상치 자동 강등** — 비지도 median HR에서 ±25 BPM 이상 벗어난 카드는 unavailable 처리

---

## 기술 스택

| 영역 | 구성 |
|------|------|
| **Backend** | Python 3.12 · FastAPI · rPPG-Toolbox (PyTorch MPS) · OpenCV · NumPy · SciPy |
| **Frontend** | React 19 · Vite · TypeScript · Tailwind v3 · TanStack Query · Zustand · Recharts |
| **얼굴 추적** | `@mediapipe/tasks-vision` (BlazeFace short-range, WASM/GPU) |
| **아키텍처** | Feature-Sliced Design (FSD) |
| **패키지** | `uv` (Python) · `pnpm` (Node) |

---

## 측정 파이프라인

```
webcam (640×480 @30fps)
   ↓
[browser] MediaPipe FaceDetector → One Euro Filter
   ↓
canvas crop (480×480, face 중앙 정렬)
   ↓
canvas.captureStream(30) → MediaRecorder → webm
   ↓
[server] FastAPI upload
   ↓
frame_decoder (frame timestamp 보존 + fps 재계산)
   ↓
face_roi (Haar cascade + box 시간평활 + 피부픽셀 게이팅, 미검출 프레임은 보간)
   ↓
12개 알고리즘 병렬 실행
   ├─ POS / CHROM / OMIT / GREEN / ICA   (RGB 채널 조합 수식)
   └─ TS-CAN / EfficientPhys / PhysFormer / RhythmFormer / BigSmall / PhysNet / DeepPhys  (PyTorch 추론)
   ↓
BVP → timestamp 기반 균일 리샘플 (VFR 보정 + ×4 업샘플 ≈120Hz)
   ↓
band-pass (0.7~3.5Hz) → Savgol smoothing → FFT HR 추정 → harmonic check
   ↓
peak detection (HR-aware distance + prominence + parabolic sub-sample 보정)
   ↓
IBI 시계열 (missed-beat 분할 복원 + ±30% window + 2·MAD 정제)
   ↓
HRV 메트릭: HR, SDNN, RMSSD, pNN50, LF/HF, Poincaré, Baevsky SI
   ↓
측정 신뢰도(beat 수·길이·SNR) 기반 적응형 컴포넌트 가중
   ↓
Composite stress v1(클래식 3) · v2(자율신경 9) · v3(전체 12) · v4(카메라 적응형 8) → 0~100
   ↓
Reliability-weighted median consensus
```

자세한 수식·근거는 `docs/specs/2026-05-29-rppg-stress-demo-design.md` 참조.

---

## 빠른 시작

### 사전 요구사항

- macOS / Linux (Apple Silicon은 PyTorch MPS 가속)
- Python 3.12+, [uv](https://github.com/astral-sh/uv)
- Node 18+, [pnpm](https://pnpm.io)
- 웹캠 + Chrome/Edge (HTTPS 또는 `localhost`에서만 작동)

### 1. 클론 (서브모듈 포함)

```bash
git clone --recurse-submodules https://github.com/seungmanchoi/rppg-stress-demo.git
cd rppg-stress-demo
```

이미 받은 뒤라면:

```bash
git submodule update --init --recursive
```

### 2. Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

> Supervised 모델 가중치는 rPPG-Toolbox 저장소(`backend/rppg_toolbox/final_model_release/`)의 사전학습 weight를 사용합니다.

### 3. Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

브라우저에서 [http://localhost:5173](http://localhost:5173) 접속.

### 4. 사용법

1. **카메라 켜기** → MediaPipe 모델 로드 (~1MB CDN)
2. 얼굴이 화면 가운데 자동 정렬되면 "얼굴 추적 중" 표시
3. **녹화 시간 선택** (15/30/45/60초) → "녹화 시작"
4. 녹화 종료 직후 자동 업로드 → 12개 알고리즘 분석 (≈ 30초 영상 기준 30~40초 소요)
5. 결과: 합의 점수 게이지(v1~v4) + 12개 카드별 HRV/스트레스/신뢰도

---

## 측정 권장 자세

- 정면 응시, 카메라에서 약 50cm
- 균일·간접 조명 (측면 직사광 X)
- 머리 / 표정 고정, 자연 호흡
- 20초 이상 안정 신호 필요 (최소 IBI 16개)

흔들거나 말하면 카드 신뢰도가 떨어지고 합의에서 자동 제외됩니다.

---

## 12개 알고리즘

| ID | 종류 | 학습 데이터 | 특징 |
|------|-----|------------|------|
| **POS** | 비지도 | — | 피부 톤 직교 평면 투영 (de Haan 2014). 가장 robust |
| **CHROM** | 비지도 | — | 색차 신호화 (de Haan 2013) |
| **OMIT** | 비지도 | — | 직교 행렬 변환, 조명 변화 robust |
| **GREEN** | 비지도 | — | 녹색 채널만 사용 — rPPG의 시초 (Verkruysse 2008) |
| **ICA** | 비지도 | — | 독립성분분석 blind source separation (Poh 2010) |
| **TS-CAN** | 지도 (CNN+TSM) | UBFC-rPPG | 모바일 실시간 친화 |
| **EfficientPhys** | 지도 (경량 CNN) | UBFC-rPPG | 가장 빠른 supervised |
| **PhysFormer** | 지도 (Video Transformer) | PURE | temporal self-attention SOTA |
| **RhythmFormer** | 지도 (Freq-domain Attention) | PURE | HRV 안정성 ↑ |
| **BigSmall** | 지도 (Multi-task CNN) | BP4D | BVP + 호흡 + AU 동시 추정 |
| **PhysNet** | 지도 (3D-CNN) | PURE | 시공간 encoder-decoder baseline (Yu 2019) |
| **DeepPhys** | 지도 (CNN+Attention) | UBFC-rPPG | motion+appearance 2-stream — TS-CAN의 원조 (Chen 2018) |

---

## 스트레스 점수 산출 (요약)

네 가지 점수를 동시에 산출합니다. **v1**(클래식 3지표) → **v2**(자율신경 9지표) → **v3**(전체 HRV 12지표)는 사용하는 지표 개수가 다르고, **v4**는 실제 카메라 단기 측정에 최적화된 적응형 robust 점수입니다.

```
# v1 — 클래식 (ESC/NASPE 1996 + Baevsky)
norm_baev  = clamp(log10(BaevSI/40) / log10(1500/40), 0, 1)
norm_lfhf  = clamp((LF/HF  - 0.7)  / (4.0  - 0.7), 0, 1)
norm_rmssd = 1 - clamp((RMSSD - 15) / (100 - 15), 0, 1)   # 역방향 (큰 RMSSD = 이완)

stress = 100 × (0.4·norm_baev + 0.4·norm_lfhf + 0.2·norm_rmssd)
```

**적응형 신뢰도 가중 (v1~v4 공통).** 30초 webcam 측정에서 LF/HF·DFA·SampEn 같은 장기·고비트 지표는 신뢰도가 낮습니다. 각 지표에 측정 길이·beat 수·SNR로 산출한 신뢰도(0~1)를 곱하고 살아남은 가중치를 재정규화해, 그 측정이 실제로 뒷받침할 수 있는 지표 위주로 점수가 형성됩니다 (지표가 부실하면 LF/HF 비중이 자동으로 줄어듭니다).

**v4 — 카메라 적응형 robust.** 단기에 빨리 안정되고 카메라 노이즈에 강한 지표(RMSSD·HF·Baevsky·Poincaré SD2/SD1·coherence)에 무게를 싣고, LF/HF·SampEn은 낮은 기본 가중으로 둡니다. 추가로 SNR이 낮거나 beat가 적으면 점수를 중립(≈38)으로 수렴시켜, 신뢰할 수 없는 측정에서 극단값 대신 "판단 보류 ≈ 보통"을 보고합니다.

| 구간 | 라벨 | 의미 |
|------|------|------|
| 0–30 | 낮음 | 이완 — 부교감 우세 |
| 30–60 | 보통 | 약한 긴장 — 일상 균형 |
| 60–80 | 높음 | 스트레스 상승 — 교감 우세 |
| 80–100 | 매우 높음 | 자율신경 불균형 |

---

## 디렉토리 구조

```
backend/
├── app/
│   ├── api/v1/measurements.py         # 업로드 + SSE 진행률
│   ├── pipeline/
│   │   ├── orchestrator.py            # 12개 알고리즘 병렬 + HRV/스트레스
│   │   ├── preprocess/                # frame_decoder, face_roi, quality_gate
│   │   ├── algorithms/                # unsupervised + supervised 어댑터
│   │   ├── hrv/                       # peak_detect, time/freq/nonlinear
│   │   ├── stress/                    # baevsky, composite
│   │   ├── reliability/               # scoring, snr
│   │   └── consensus.py               # reliability-weighted median
│   └── models/                        # 가중치 로더
├── rppg_toolbox/                      # submodule
└── tests/                             # 45 tests

frontend/
└── src/
    ├── pages/measure/                 # 메인 페이지
    ├── widgets/                       # consensus-dashboard, stress-formula, …
    ├── features/
    │   ├── record-video/              # webcam + face tracker + recorder
    │   ├── run-measurement/           # SSE 진행률 + 결과 store
    │   └── algorithm-result-card/     # 알고리즘 카드 UI
    ├── entities/algorithm/            # 알고리즘 메타데이터
    └── shared/                        # api, lib, ui
```

---

## 테스트

```bash
cd backend
uv run pytest -q     # 45 tests
```

```bash
cd frontend
pnpm run build       # tsc + vite build
```

---

## 설계 / 구현 문서

- `docs/specs/2026-05-29-rppg-stress-demo-design.md` — 전체 설계 13개 섹션
- `docs/plans/2026-05-29-rppg-stress-demo.md` — 12단계 구현 계획

---

## 라이선스 / 출처

- [rPPG-Toolbox](https://github.com/ubicomplab/rPPG-Toolbox) (Apache-2.0) — 알고리즘 구현 + 사전학습 가중치
- [MediaPipe Tasks Vision](https://developers.google.com/mediapipe) — 얼굴 검출
- 본 데모 코드: 교육·연구 목적 자유 사용

> ⚠ 본 데모는 의료기기가 아닙니다. 결과는 추정치이며 진단·치료에 사용할 수 없습니다.
