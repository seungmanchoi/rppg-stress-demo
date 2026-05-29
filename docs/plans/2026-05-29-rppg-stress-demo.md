# rPPG Stress Demo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** rPPG-Toolbox 기반 영상 업로드 → 8개 알고리즘 동시 추출 → 통합 스트레스 지수 + 신뢰도 표시 데모를 FastAPI + React/Vite + FSD로 구현한다.

**Architecture:** FastAPI 백엔드가 mp4를 받아 MediaPipe로 얼굴 ROI를 추출하고, 8개의 rPPG 알고리즘(POS·CHROM·OMIT·TS-CAN·EfficientPhys·PhysFormer·RhythmFormer·BigSmall)을 병렬 실행한 뒤 IBI → HRV → Baevsky/LF·HF/Composite 스트레스 지수 + Reliability를 산출하여 JSON으로 반환. React FSD 프론트엔드가 상단 통합 대시보드 + 4×2 알고리즘 카드 그리드로 표시.

**Tech Stack:** Python 3.11 · FastAPI · PyTorch (MPS) · OpenCV · MediaPipe · SciPy · rPPG-Toolbox / React 18 · Vite · TypeScript · TanStack Query · Zustand · Tailwind · shadcn/ui · Recharts · Playwright

**Spec reference:** `docs/specs/2026-05-29-rppg-stress-demo-design.md`

---

## File Structure (작업 시 생성/수정 대상)

```
rppg-stress-demo/
├─ .git/                              # Phase 0
├─ .gitignore                         # Phase 0
├─ README.md                          # Phase 0
├─ backend/
│  ├─ pyproject.toml                  # Phase 0
│  ├─ app/
│  │  ├─ main.py                      # Phase 7
│  │  ├─ api/v1/
│  │  │  ├─ measurements.py           # Phase 7
│  │  │  ├─ algorithms.py             # Phase 7
│  │  │  └─ health.py                 # Phase 7
│  │  ├─ core/
│  │  │  ├─ config.py                 # Phase 0
│  │  │  ├─ jobs.py                   # Phase 6
│  │  │  └─ events.py                 # Phase 7
│  │  ├─ schemas/
│  │  │  ├─ measurement.py            # Phase 7
│  │  │  └─ algorithm.py              # Phase 7
│  │  ├─ models/registry.py           # Phase 5
│  │  ├─ pipeline/
│  │  │  ├─ orchestrator.py           # Phase 6
│  │  │  ├─ preprocess/
│  │  │  │  ├─ frame_decoder.py       # Phase 4
│  │  │  │  ├─ face_roi.py            # Phase 4
│  │  │  │  └─ quality_gate.py        # Phase 4
│  │  │  ├─ algorithms/
│  │  │  │  ├─ base.py                # Phase 5
│  │  │  │  ├─ unsupervised/{pos,chrom,omit}.py    # Phase 5
│  │  │  │  └─ supervised/{ts_can,efficientphys,physformer,rhythmformer,bigsmall}.py # Phase 5
│  │  │  ├─ hrv/
│  │  │  │  ├─ peak_detect.py         # Phase 1
│  │  │  │  ├─ time_domain.py         # Phase 1
│  │  │  │  ├─ freq_domain.py         # Phase 1
│  │  │  │  └─ nonlinear.py           # Phase 1
│  │  │  ├─ stress/
│  │  │  │  ├─ baevsky.py             # Phase 2
│  │  │  │  └─ composite.py           # Phase 2
│  │  │  └─ reliability/
│  │  │     ├─ snr.py                 # Phase 3
│  │  │     ├─ tracking.py            # Phase 3
│  │  │     └─ scoring.py             # Phase 3
│  │  └─ utils/weights_downloader.py  # Phase 8
│  ├─ rppg_toolbox/                   # Phase 5 (git submodule)
│  ├─ weights/                        # gitignored
│  ├─ tests/                          # Phase 1~12
│  └─ scripts/{download_weights,benchmark}.py    # Phase 8
└─ frontend/
   ├─ package.json                    # Phase 0
   ├─ vite.config.ts                  # Phase 0
   ├─ tsconfig.json                   # Phase 0
   ├─ tailwind.config.ts              # Phase 0
   ├─ index.html                      # Phase 0
   └─ src/
      ├─ app/{App,providers/{QueryProvider,ThemeProvider}}.tsx # Phase 9
      ├─ pages/measure/MeasurePage.tsx          # Phase 11
      ├─ pages/about/AboutPage.tsx              # Phase 11
      ├─ widgets/
      │  ├─ consensus-dashboard/                # Phase 11
      │  ├─ algorithm-cards-grid/               # Phase 11
      │  └─ measurement-progress/               # Phase 11
      ├─ features/
      │  ├─ upload-video/                       # Phase 10
      │  ├─ run-measurement/                    # Phase 10
      │  └─ algorithm-result-card/              # Phase 10
      ├─ entities/
      │  ├─ measurement/                        # Phase 9
      │  └─ algorithm/                          # Phase 9
      └─ shared/{api,ui,lib,config}/            # Phase 9
```

---

## Phase 0 — 프로젝트 부트스트랩

### Task 0.1: 저장소 초기화

**Files:**
- Create: `.gitignore`, `README.md`

- [ ] **Step 1: git init**
```bash
cd /Users/seungmanchoi/works_test/rppg-stress-demo
git init -b main
```

- [ ] **Step 2: `.gitignore` 작성**
```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
.uv/
*.egg-info/

# Weights / data
backend/weights/
backend/tests/fixtures/*.mp4
backend/tests/fixtures/*.npy

# Node
node_modules/
dist/
.vite/

# Misc
.DS_Store
.env
.env.local
*.log
/tmp/
```

- [ ] **Step 3: `README.md` 작성 (간단 한 줄 요약)**
```markdown
# rPPG Stress Demo
영상 업로드 기반 비접촉 심박/HRV/스트레스 지수 데모. 자세한 설계: `docs/specs/2026-05-29-rppg-stress-demo-design.md`.
```

- [ ] **Step 4: 커밋**
```bash
git add .gitignore README.md docs/
git commit -m "chore: bootstrap repo, add design spec and plan"
```

### Task 0.2: 백엔드 uv 프로젝트 셋업

**Files:**
- Create: `backend/pyproject.toml`, `backend/app/__init__.py`, `backend/app/core/config.py`

- [ ] **Step 1: uv 초기화**
```bash
cd backend && uv init --package --name rppg-stress-api --python 3.11
```

- [ ] **Step 2: 의존성 추가**
```bash
uv add fastapi 'uvicorn[standard]' pydantic pydantic-settings \
       torch torchvision opencv-python mediapipe scipy numpy \
       sse-starlette python-multipart httpx
uv add --dev pytest pytest-asyncio pytest-cov ruff mypy
```

- [ ] **Step 3: `app/core/config.py`**
```python
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="RPPG_")

    project_root: Path = Path(__file__).resolve().parent.parent.parent
    weights_dir: Path = project_root / "weights"
    tmp_dir: Path = Path("/tmp/rppg_measurements")
    max_video_mb: int = 200
    min_video_seconds: float = 10.0
    max_video_seconds: float = 120.0
    target_fps: int = 30
    job_ttl_seconds: int = 3600
    cors_origins: list[str] = ["http://localhost:5173"]

settings = Settings()
settings.weights_dir.mkdir(parents=True, exist_ok=True)
settings.tmp_dir.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: smoke 테스트**
```bash
uv run python -c "from app.core.config import settings; print(settings.weights_dir)"
```
Expected: `/.../backend/weights` 출력

- [ ] **Step 5: 커밋**
```bash
git add backend/
git commit -m "feat(backend): scaffold FastAPI project with uv and base settings"
```

### Task 0.3: 프론트엔드 Vite 프로젝트 셋업

**Files:** `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tailwind.config.ts`, `frontend/postcss.config.js`, `frontend/index.html`, `frontend/src/app/styles/global.css`, `frontend/src/main.tsx`

- [ ] **Step 1: Vite scaffold + 의존성**
```bash
cd /Users/seungmanchoi/works_test/rppg-stress-demo
pnpm create vite frontend --template react-ts
cd frontend
pnpm add @tanstack/react-query zustand react-dropzone recharts \
        clsx tailwind-merge class-variance-authority
pnpm add -D tailwindcss postcss autoprefixer @types/node \
            vitest @testing-library/react @testing-library/jest-dom jsdom \
            @playwright/test
pnpm dlx tailwindcss init -p
```

- [ ] **Step 2: `tailwind.config.ts`**
```ts
import type { Config } from 'tailwindcss';
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: { extend: {} },
  plugins: [],
} satisfies Config;
```

- [ ] **Step 3: `src/app/styles/global.css`**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root { color-scheme: light dark; }
body { @apply bg-neutral-50 text-neutral-900 antialiased; }
```

- [ ] **Step 4: vite alias 설정 (FSD 임포트 경로)** — `vite.config.ts`
```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@app': path.resolve(__dirname, 'src/app'),
      '@pages': path.resolve(__dirname, 'src/pages'),
      '@widgets': path.resolve(__dirname, 'src/widgets'),
      '@features': path.resolve(__dirname, 'src/features'),
      '@entities': path.resolve(__dirname, 'src/entities'),
      '@shared': path.resolve(__dirname, 'src/shared'),
    },
  },
  server: { port: 5173 },
});
```

- [ ] **Step 5: tsconfig paths 동기화** — `tsconfig.json`에 `compilerOptions.paths`에 동일 alias 추가

- [ ] **Step 6: smoke 실행**
```bash
pnpm dev
```
Expected: localhost:5173에서 Vite 기본 페이지 표시

- [ ] **Step 7: 커밋**
```bash
git add frontend/
git commit -m "feat(frontend): scaffold Vite + React + TS with Tailwind and FSD aliases"
```

### Task 0.4: FSD 디렉토리 골격 생성

- [ ] **Step 1: 빈 폴더 + barrel 파일 생성**
```bash
cd frontend/src
for d in app/providers pages/measure pages/about \
         widgets/consensus-dashboard/ui widgets/algorithm-cards-grid/ui widgets/measurement-progress/ui \
         features/upload-video/{ui,model} features/run-measurement/model features/algorithm-result-card/ui \
         entities/measurement/model entities/algorithm/model \
         shared/{api,ui,lib,config}; do
  mkdir -p "$d"
done
find . -type d -mindepth 1 -exec sh -c 'test -f "$1/index.ts" || echo "export {}" > "$1/index.ts"' _ {} \;
```

- [ ] **Step 2: 커밋**
```bash
git add frontend/src
git commit -m "chore(frontend): create FSD directory skeleton"
```

---

## Phase 1 — HRV 코어 (TDD)

### Task 1.1: IBI peak detection

**Files:**
- Create: `backend/app/pipeline/hrv/peak_detect.py`
- Test: `backend/tests/test_peak_detect.py`

- [ ] **Step 1: 실패 테스트 작성**
```python
# backend/tests/test_peak_detect.py
import numpy as np
from app.pipeline.hrv.peak_detect import bvp_to_ibi

def test_synthetic_sine_60bpm_yields_1000ms_ibi():
    fs = 30
    t = np.arange(0, 30, 1/fs)
    bvp = np.sin(2 * np.pi * 1.0 * t)  # 1 Hz = 60 BPM
    ibi_ms = bvp_to_ibi(bvp, fs=fs)
    assert 950 < np.mean(ibi_ms) < 1050
    assert len(ibi_ms) >= 25
```

- [ ] **Step 2: 테스트 실패 확인**
```bash
uv run pytest tests/test_peak_detect.py -v
```
Expected: ModuleNotFoundError

- [ ] **Step 3: 최소 구현**
```python
# backend/app/pipeline/hrv/peak_detect.py
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks

def bandpass(signal: np.ndarray, fs: float, lo: float = 0.7, hi: float = 3.5) -> np.ndarray:
    nyq = fs / 2
    b, a = butter(3, [lo / nyq, hi / nyq], btype="band")
    return filtfilt(b, a, signal)

def bvp_to_ibi(bvp: np.ndarray, fs: float) -> np.ndarray:
    """BVP waveform → IBI series in milliseconds. Removes outliers via median ± 3·MAD."""
    filtered = bandpass(bvp, fs)
    peaks, _ = find_peaks(filtered, distance=int(0.4 * fs))
    if len(peaks) < 2:
        return np.array([])
    ibi_ms = np.diff(peaks) / fs * 1000.0

    if len(ibi_ms) >= 3:
        med = np.median(ibi_ms)
        mad = np.median(np.abs(ibi_ms - med)) or 1.0
        ibi_ms = ibi_ms[np.abs(ibi_ms - med) < 3 * mad]
    return ibi_ms
```

- [ ] **Step 4: 테스트 통과 확인**
```bash
uv run pytest tests/test_peak_detect.py -v
```
Expected: PASS

- [ ] **Step 5: 커밋**
```bash
git add backend/app/pipeline/hrv/peak_detect.py backend/tests/test_peak_detect.py
git commit -m "feat(hrv): BVP → IBI peak detection with outlier removal"
```

### Task 1.2: Time-domain HRV (SDNN/RMSSD/pNN50)

**Files:**
- Create: `backend/app/pipeline/hrv/time_domain.py`
- Test: `backend/tests/test_hrv_time.py`

- [ ] **Step 1: 실패 테스트**
```python
import numpy as np
from app.pipeline.hrv.time_domain import time_domain_hrv

def test_known_ibi_series():
    ibi_ms = np.array([900, 920, 880, 910, 905, 895, 915, 890])
    m = time_domain_hrv(ibi_ms)
    assert abs(m.sdnn_ms - np.std(ibi_ms)) < 0.5
    assert m.rmssd_ms > 0
    assert 0 <= m.pnn50_pct <= 100
    assert 60_000 / m.hr_bpm == approx_close(np.mean(ibi_ms))

def approx_close(target):
    class _A:
        def __eq__(self, other): return abs(other - target) < 5
    return _A()
```

- [ ] **Step 2: 테스트 실패 확인**
```bash
uv run pytest tests/test_hrv_time.py -v
```

- [ ] **Step 3: 구현**
```python
# backend/app/pipeline/hrv/time_domain.py
from dataclasses import dataclass
import numpy as np

@dataclass
class TimeDomainHRV:
    hr_bpm: float
    ibi_mean_ms: float
    sdnn_ms: float
    rmssd_ms: float
    pnn50_pct: float

def time_domain_hrv(ibi_ms: np.ndarray) -> TimeDomainHRV:
    if len(ibi_ms) < 2:
        return TimeDomainHRV(0, 0, 0, 0, 0)
    diffs = np.diff(ibi_ms)
    return TimeDomainHRV(
        hr_bpm=float(60_000 / np.mean(ibi_ms)),
        ibi_mean_ms=float(np.mean(ibi_ms)),
        sdnn_ms=float(np.std(ibi_ms)),
        rmssd_ms=float(np.sqrt(np.mean(diffs ** 2))),
        pnn50_pct=float(np.sum(np.abs(diffs) > 50) / len(diffs) * 100),
    )
```

- [ ] **Step 4: PASS 확인**

- [ ] **Step 5: 커밋**
```bash
git add backend/app/pipeline/hrv/time_domain.py backend/tests/test_hrv_time.py
git commit -m "feat(hrv): time-domain metrics (HR, SDNN, RMSSD, pNN50)"
```

### Task 1.3: Frequency-domain HRV (Lomb-Scargle)

**Files:**
- Create: `backend/app/pipeline/hrv/freq_domain.py`
- Test: `backend/tests/test_hrv_freq.py`

- [ ] **Step 1: 실패 테스트**
```python
import numpy as np
from app.pipeline.hrv.freq_domain import freq_domain_hrv

def test_synthetic_hf_dominant():
    # 0.25 Hz HF 주기 변동 + 1Hz 기본 RR
    n = 240
    t = np.cumsum(np.full(n, 1000.0) + 30 * np.sin(2 * np.pi * 0.25 * np.arange(n)))
    ibi = np.diff(t)
    m = freq_domain_hrv(ibi)
    assert m.hf_power > m.lf_power
    assert m.lf_hf_ratio < 1.0
```

- [ ] **Step 2: 실패 확인**

- [ ] **Step 3: 구현**
```python
# backend/app/pipeline/hrv/freq_domain.py
from dataclasses import dataclass
import numpy as np
from scipy.signal import lombscargle

@dataclass
class FreqDomainHRV:
    lf_power: float
    hf_power: float
    lf_hf_ratio: float

def freq_domain_hrv(ibi_ms: np.ndarray) -> FreqDomainHRV:
    if len(ibi_ms) < 16:
        return FreqDomainHRV(0, 0, 0)
    t = np.cumsum(ibi_ms) / 1000.0
    x = ibi_ms - np.mean(ibi_ms)
    freqs = np.linspace(0.04, 0.4, 256)
    psd = lombscargle(t, x, freqs * 2 * np.pi, normalize=True)
    lf_mask = (freqs >= 0.04) & (freqs < 0.15)
    hf_mask = (freqs >= 0.15) & (freqs <= 0.40)
    lf = float(np.trapz(psd[lf_mask], freqs[lf_mask]))
    hf = float(np.trapz(psd[hf_mask], freqs[hf_mask]))
    ratio = lf / hf if hf > 1e-12 else 0.0
    return FreqDomainHRV(lf, hf, ratio)
```

- [ ] **Step 4: PASS 확인**

- [ ] **Step 5: 커밋**
```bash
git add backend/app/pipeline/hrv/freq_domain.py backend/tests/test_hrv_freq.py
git commit -m "feat(hrv): frequency-domain metrics via Lomb-Scargle"
```

### Task 1.4: Non-linear (Poincaré SD1/SD2)

**Files:**
- Create: `backend/app/pipeline/hrv/nonlinear.py`
- Test: `backend/tests/test_hrv_nonlinear.py`

- [ ] **Step 1: 실패 테스트**
```python
import numpy as np
from app.pipeline.hrv.nonlinear import poincare

def test_poincare_basic():
    rng = np.random.default_rng(42)
    ibi = 900 + rng.normal(0, 25, 200)
    p = poincare(ibi)
    assert p.sd1 > 0 and p.sd2 > 0
    assert p.sd2 >= p.sd1 * 0.5
```

- [ ] **Step 2~5:** 구현, PASS, commit
```python
# backend/app/pipeline/hrv/nonlinear.py
from dataclasses import dataclass
import numpy as np

@dataclass
class Poincare:
    sd1: float
    sd2: float

def poincare(ibi_ms: np.ndarray) -> Poincare:
    if len(ibi_ms) < 3:
        return Poincare(0, 0)
    x1, x2 = ibi_ms[:-1], ibi_ms[1:]
    sd1 = float(np.std(x2 - x1) / np.sqrt(2))
    sd2 = float(np.std(x2 + x1) / np.sqrt(2))
    return Poincare(sd1, sd2)
```
```bash
git add backend/app/pipeline/hrv/nonlinear.py backend/tests/test_hrv_nonlinear.py
git commit -m "feat(hrv): non-linear Poincaré SD1/SD2"
```

---

## Phase 2 — 스트레스 산출

### Task 2.1: Baevsky Stress Index

**Files:** `backend/app/pipeline/stress/baevsky.py`, `backend/tests/test_baevsky.py`

- [ ] **Step 1: 실패 테스트**
```python
import numpy as np
from app.pipeline.stress.baevsky import baevsky_si, baevsky_level

def test_baevsky_low_for_relaxed():
    ibi_ms = 900 + 30 * np.sin(np.linspace(0, 6 * np.pi, 200))
    out = baevsky_si(ibi_ms)
    assert 30 < out.si < 800   # 합성 신호 기준 합리적 범위
    assert out.level in {"normal", "mild", "moderate"}

def test_baevsky_high_for_rigid():
    ibi_ms = np.full(200, 700.0) + np.random.default_rng(0).normal(0, 1, 200)
    out = baevsky_si(ibi_ms)
    assert out.si > 500
    assert out.level in {"moderate", "high"}
```

- [ ] **Step 2: 실패 확인**

- [ ] **Step 3: 구현**
```python
# backend/app/pipeline/stress/baevsky.py
from dataclasses import dataclass
from typing import Literal
import numpy as np

Level = Literal["normal", "mild", "moderate", "high"]

@dataclass
class BaevskyResult:
    si: float
    level: Level

def baevsky_level(si: float) -> Level:
    if si < 150: return "normal"
    if si < 500: return "mild"
    if si < 900: return "moderate"
    return "high"

def baevsky_si(ibi_ms: np.ndarray) -> BaevskyResult:
    if len(ibi_ms) < 16:
        return BaevskyResult(0.0, "normal")
    ibi_s = ibi_ms / 1000.0
    bin_width = 0.05
    bins = np.arange(ibi_s.min(), ibi_s.max() + bin_width, bin_width)
    counts, edges = np.histogram(ibi_s, bins=bins)
    if counts.sum() == 0:
        return BaevskyResult(0.0, "normal")
    mode_idx = int(np.argmax(counts))
    mo = float((edges[mode_idx] + edges[mode_idx + 1]) / 2)
    amo = float(counts[mode_idx] / counts.sum() * 100)
    mxdmn = float(ibi_s.max() - ibi_s.min()) or 1e-6
    si = amo / (2 * mo * mxdmn)
    return BaevskyResult(si=si, level=baevsky_level(si))
```

- [ ] **Step 4: PASS**

- [ ] **Step 5: commit**
```bash
git commit -am "feat(stress): Baevsky Stress Index"
```

### Task 2.2: Composite stress score

**Files:** `backend/app/pipeline/stress/composite.py`, `backend/tests/test_composite.py`

- [ ] **Step 1: 실패 테스트**
```python
from app.pipeline.stress.composite import composite_stress, composite_level

def test_composite_range_and_level():
    score = composite_stress(baevsky_si=300, lf_hf=2.0, rmssd=30)
    assert 0 <= score <= 100
    assert composite_level(score) in {"low", "mid", "high", "very_high"}

def test_high_stress_input():
    score = composite_stress(baevsky_si=1200, lf_hf=4.0, rmssd=10)
    assert score > 60
```

- [ ] **Step 2: 실패 확인**

- [ ] **Step 3: 구현**
```python
# backend/app/pipeline/stress/composite.py
from typing import Literal
import math

Level = Literal["low", "mid", "high", "very_high"]

def _clip(v: float, lo: float = 0, hi: float = 1) -> float:
    return max(lo, min(hi, v))

def composite_stress(baevsky_si: float, lf_hf: float, rmssd: float) -> float:
    s_baev = _clip(math.log10(max(baevsky_si, 1) / 50) / math.log10(1500 / 50))
    s_lfhf = _clip((lf_hf - 0.5) / 4.0)
    s_rmssd = _clip(1 - rmssd / 60)
    return 100 * (0.4 * s_baev + 0.4 * s_lfhf + 0.2 * s_rmssd)

def composite_level(score: float) -> Level:
    if score < 30: return "low"
    if score < 60: return "mid"
    if score < 80: return "high"
    return "very_high"
```

- [ ] **Step 4~5: PASS + commit**

---

## Phase 3 — Reliability

### Task 3.1: SNR

**Files:** `backend/app/pipeline/reliability/snr.py`, `backend/tests/test_snr.py`

- [ ] **Step 1: 실패 테스트**
```python
import numpy as np
from app.pipeline.reliability.snr import bvp_snr_db

def test_clean_signal_high_snr():
    fs = 30
    t = np.arange(0, 30, 1/fs)
    clean = np.sin(2 * np.pi * 1.2 * t)
    noisy = clean + np.random.default_rng(0).normal(0, 0.05, len(t))
    assert bvp_snr_db(clean, fs) > bvp_snr_db(noisy, fs)
```

- [ ] **Step 2: 실패 확인**

- [ ] **Step 3: 구현**
```python
# backend/app/pipeline/reliability/snr.py
import numpy as np
from scipy.signal import welch

def bvp_snr_db(bvp: np.ndarray, fs: float) -> float:
    """SNR: power in 0.7~3 Hz band vs total power outside, in dB."""
    f, psd = welch(bvp, fs=fs, nperseg=min(len(bvp), int(fs * 8)))
    sig_mask = (f >= 0.7) & (f <= 3.0)
    sig_power = float(np.trapz(psd[sig_mask], f[sig_mask]))
    noise_power = float(np.trapz(psd[~sig_mask], f[~sig_mask])) or 1e-12
    return 10 * float(np.log10(sig_power / noise_power))
```

- [ ] **Step 4~5: PASS + commit**

### Task 3.2: Tracking score (얼굴 검출 비율)

**Files:** `backend/app/pipeline/reliability/tracking.py`, `backend/tests/test_tracking.py`

- [ ] **Step 1~5:** 단순 비율 계산
```python
# tracking.py
def tracking_score(detected_frames: int, total_frames: int) -> float:
    return float(detected_frames / total_frames) if total_frames else 0.0
```
```python
# test
from app.pipeline.reliability.tracking import tracking_score
def test_tracking(): assert tracking_score(90, 100) == 0.9
```
commit: `feat(reliability): face tracking ratio`

### Task 3.3: Reliability composite + 등급

**Files:** `backend/app/pipeline/reliability/scoring.py`, `backend/tests/test_reliability.py`

- [ ] **Step 1: 실패 테스트**
```python
from app.pipeline.reliability.scoring import reliability_score, reliability_grade

def test_high_reliability():
    s = reliability_score(snr_db=10, tracking=0.95, motion_px=1, hr_dev=2)
    assert s > 75
    assert reliability_grade(s) == "high"

def test_low_reliability():
    s = reliability_score(snr_db=-3, tracking=0.5, motion_px=8, hr_dev=12)
    assert s < 45
    assert reliability_grade(s) == "low"
```

- [ ] **Step 2~5:**
```python
# scoring.py
from typing import Literal
Grade = Literal["low", "medium", "high"]

def _clip(v, lo=0.0, hi=1.0): return max(lo, min(hi, v))

def reliability_score(snr_db: float, tracking: float, motion_px: float, hr_dev: float) -> float:
    snr = _clip((snr_db + 5) / 15)
    track = _clip(tracking)
    motion = _clip(1 - motion_px / 5)
    consensus = _clip(1 - abs(hr_dev) / 10)
    return 100 * (0.30 * snr + 0.25 * track + 0.20 * motion + 0.25 * consensus)

def reliability_grade(score: float) -> Grade:
    if score >= 75: return "high"
    if score >= 45: return "medium"
    return "low"
```
commit: `feat(reliability): composite scoring and grading`

---

## Phase 4 — 전처리 파이프라인

### Task 4.1: Frame decoder

**Files:** `backend/app/pipeline/preprocess/frame_decoder.py`, `backend/tests/test_frame_decoder.py`

- [ ] **Step 1: 테스트 (실제 mp4 fixture 사용 — `tests/fixtures/sample_10s.mp4`)**
```python
from pathlib import Path
from app.pipeline.preprocess.frame_decoder import decode_video

def test_decode_returns_frames_and_fps(tmp_path):
    sample = Path("tests/fixtures/sample_10s.mp4")
    frames, fps, (h, w) = decode_video(sample, target_fps=30)
    assert frames.ndim == 4 and frames.shape[-1] == 3
    assert 28 <= fps <= 32
    assert h > 0 and w > 0
```

- [ ] **Step 2~5: 구현 + commit**
```python
# frame_decoder.py
from pathlib import Path
import cv2
import numpy as np

def decode_video(path: Path, target_fps: int = 30) -> tuple[np.ndarray, float, tuple[int, int]]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {path}")
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    stride = max(1, int(round(src_fps / target_fps)))
    frames: list[np.ndarray] = []
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok: break
        if idx % stride == 0:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        idx += 1
    cap.release()
    if not frames:
        raise ValueError("No frames decoded")
    arr = np.stack(frames, axis=0)
    fps = src_fps / stride
    return arr, float(fps), arr.shape[1:3]
```
commit: `feat(preprocess): video frame decoder with target fps`

### Task 4.2: Face ROI extraction (MediaPipe)

**Files:** `backend/app/pipeline/preprocess/face_roi.py`, `backend/tests/test_face_roi.py`

- [ ] **Step 1: 테스트 (한 프레임에 대해 ROI 좌표가 frame 안에 있는지)**

- [ ] **Step 2~5: 구현**
```python
# face_roi.py
import numpy as np
import mediapipe as mp

# 이마 + 양 볼 landmark 인덱스
FOREHEAD = [10, 67, 297, 332, 338]
LEFT_CHEEK = [50, 101, 118, 117, 123]
RIGHT_CHEEK = [280, 330, 347, 346, 352]

_face_mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, refine_landmarks=False)

def extract_roi_signal(frames: np.ndarray) -> tuple[np.ndarray, int]:
    """frames: (T, H, W, 3) RGB → (T, 3) mean RGB over ROI, detected_count."""
    T, H, W, _ = frames.shape
    signal = np.zeros((T, 3))
    detected = 0
    for i in range(T):
        res = _face_mesh.process(frames[i])
        if not res.multi_face_landmarks:
            signal[i] = signal[i - 1] if i > 0 else 0
            continue
        lms = res.multi_face_landmarks[0].landmark
        pts = np.array([(int(lms[j].x * W), int(lms[j].y * H)) for j in FOREHEAD + LEFT_CHEEK + RIGHT_CHEEK])
        x0, y0 = pts.min(0); x1, y1 = pts.max(0)
        roi = frames[i, y0:y1, x0:x1]
        if roi.size:
            signal[i] = roi.reshape(-1, 3).mean(0)
            detected += 1
    return signal, detected
```
commit: `feat(preprocess): MediaPipe face ROI extraction`

### Task 4.3: Quality gate

**Files:** `backend/app/pipeline/preprocess/quality_gate.py`, `backend/tests/test_quality_gate.py`

- [ ] **Step 1~5:** 검출 비율 + 평균 brightness + optical flow 평균 → warnings 리스트 반환
```python
# quality_gate.py
from dataclasses import dataclass
import numpy as np
import cv2

@dataclass
class QualityReport:
    detected_ratio: float
    mean_brightness: float
    mean_motion_px: float
    warnings: list[str]

def assess(frames: np.ndarray, detected: int) -> QualityReport:
    total = len(frames)
    ratio = detected / total if total else 0
    brightness = float(frames.mean())
    grays = [cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in frames[::5]]
    flow = []
    for a, b in zip(grays, grays[1:]):
        f = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        flow.append(float(np.linalg.norm(f, axis=-1).mean()))
    motion = float(np.mean(flow)) if flow else 0.0
    warnings = []
    if ratio < 0.7: warnings.append(f"얼굴 검출 비율 낮음: {ratio:.0%}")
    if brightness < 50: warnings.append("영상이 어두움")
    if motion > 3: warnings.append("움직임 큼")
    return QualityReport(ratio, brightness, motion, warnings)
```
commit: `feat(preprocess): quality gate (tracking, brightness, motion)`

---

## Phase 5 — 알고리즘 어댑터

### Task 5.1: Abstract base + algorithm registry

**Files:** `backend/app/pipeline/algorithms/base.py`, `backend/app/models/registry.py`, `backend/tests/test_registry.py`

- [ ] **Step 1: 실패 테스트**
```python
from app.models.registry import ALGORITHMS, get_meta

def test_registry_has_eight():
    assert len(ALGORITHMS) == 8
    assert {a.id for a in ALGORITHMS} == {
        "POS","CHROM","OMIT","TS-CAN","EfficientPhys","PhysFormer","RhythmFormer","BigSmall"
    }
    assert get_meta("POS").type == "unsupervised"
```

- [ ] **Step 2~5: 구현 + commit**
```python
# registry.py
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class AlgorithmMeta:
    id: str
    display_name: str
    short_description: str
    type: Literal["unsupervised", "supervised"]
    backbone: str
    pretrained_on: str | None = None
    model_size_mb: int | None = None
    weight_url: str | None = None
    weight_filename: str | None = None

ALGORITHMS: list[AlgorithmMeta] = [
    AlgorithmMeta("POS","POS","피부 톤 직교 평면 투영","unsupervised","Signal processing"),
    AlgorithmMeta("CHROM","CHROM","피부 톤 표준화 후 색차 신호화","unsupervised","Signal processing"),
    AlgorithmMeta("OMIT","OMIT","Orthogonal Matrix Image Transformation","unsupervised","Signal processing"),
    AlgorithmMeta("TS-CAN","TS-CAN","2D-CNN + Temporal Shift","supervised","CNN+TSM","UBFC-rPPG",30,
                  "https://github.com/ubicomplab/rPPG-Toolbox/raw/main/final_model_release/UBFC-rPPG_TSCAN.pth",
                  "UBFC-rPPG_TSCAN.pth"),
    AlgorithmMeta("EfficientPhys","EfficientPhys","경량 CNN","supervised","Light CNN","UBFC-rPPG",25,
                  "https://github.com/ubicomplab/rPPG-Toolbox/raw/main/final_model_release/UBFC-rPPG_EfficientPhys.pth",
                  "UBFC-rPPG_EfficientPhys.pth"),
    AlgorithmMeta("PhysFormer","PhysFormer","Video Transformer","supervised","Transformer","PURE",200,
                  "https://github.com/ubicomplab/rPPG-Toolbox/raw/main/final_model_release/PURE_PhysFormer_DiffNormalized.pth",
                  "PURE_PhysFormer_DiffNormalized.pth"),
    AlgorithmMeta("RhythmFormer","RhythmFormer","주파수 영역 attention","supervised","Freq-attention","PURE",180,
                  "https://github.com/ubicomplab/rPPG-Toolbox/raw/main/final_model_release/PURE_RhythmFormer.pth",
                  "PURE_RhythmFormer.pth"),
    AlgorithmMeta("BigSmall","BigSmall","멀티태스크: BVP+호흡+AU","supervised","Multitask CNN","BP4D",80,
                  "https://github.com/ubicomplab/rPPG-Toolbox/raw/main/final_model_release/BP4D_BigSmall_Multitask_Fold1.pth",
                  "BP4D_BigSmall_Multitask_Fold1.pth"),
]

_META_BY_ID = {m.id: m for m in ALGORITHMS}
def get_meta(id: str) -> AlgorithmMeta: return _META_BY_ID[id]
```

```python
# base.py
from abc import ABC, abstractmethod
import numpy as np

class AlgorithmAdapter(ABC):
    id: str
    @abstractmethod
    def estimate_bvp(self, rgb_signal: np.ndarray, frames: np.ndarray, fs: float) -> np.ndarray: ...
```
commit: `feat(algorithms): registry of 8 algorithms + base adapter`

### Task 5.2: Unsupervised adapters (POS / CHROM / OMIT) via rPPG-Toolbox

**Files:** `backend/app/pipeline/algorithms/unsupervised/{pos,chrom,omit}.py`, tests

- [ ] **Step 1: rPPG-Toolbox submodule 추가**
```bash
cd backend
git submodule add https://github.com/ubicomplab/rPPG-Toolbox.git rppg_toolbox
git -C rppg_toolbox checkout main
```

- [ ] **Step 2: PYTHONPATH 설정 — `backend/app/pipeline/algorithms/unsupervised/__init__.py`**
```python
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[4] / "rppg_toolbox"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
```

- [ ] **Step 3: POS 어댑터**
```python
# pos.py
import numpy as np
from ..base import AlgorithmAdapter
from unsupervised_methods.methods.POS_WANG import POS_WANG

class PosAdapter(AlgorithmAdapter):
    id = "POS"
    def estimate_bvp(self, rgb_signal, frames, fs):
        return POS_WANG(rgb_signal, fs)
```

- [ ] **Step 4: 테스트 — 합성 RGB 신호로 BVP 길이 일치, 0이 아닌 값 확인**
```python
import numpy as np
from app.pipeline.algorithms.unsupervised.pos import PosAdapter
def test_pos_runs():
    rng = np.random.default_rng(0)
    sig = 128 + 5 * np.sin(np.linspace(0,30*2*np.pi*1.2, 30*30)).reshape(-1,1)*np.array([1,1,1])
    sig = sig + rng.normal(0,1,sig.shape)
    bvp = PosAdapter().estimate_bvp(sig, None, 30)
    assert len(bvp) == len(sig)
    assert np.std(bvp) > 0
```

- [ ] **Step 5: CHROM, OMIT 동일 패턴으로 작성**

- [ ] **Step 6: 커밋**
```bash
git add backend/rppg_toolbox backend/app/pipeline/algorithms/unsupervised backend/tests/test_unsup_*.py .gitmodules
git commit -m "feat(algorithms): POS/CHROM/OMIT unsupervised adapters"
```

### Task 5.3: Supervised adapters — TS-CAN, EfficientPhys

**Files:** `backend/app/pipeline/algorithms/supervised/{ts_can,efficientphys}.py`, tests

- [ ] **Step 1: 디바이스 선택 유틸 (`backend/app/pipeline/algorithms/supervised/__init__.py`)**
```python
import os, torch
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

def get_device():
    if torch.backends.mps.is_available(): return torch.device("mps")
    if torch.cuda.is_available(): return torch.device("cuda")
    return torch.device("cpu")
```

- [ ] **Step 2: TS-CAN 어댑터 (rPPG-Toolbox의 `neural_methods.model.TS_CAN` import)**
```python
# ts_can.py
import torch, numpy as np
from neural_methods.model.TS_CAN import TSCAN
from app.core.config import settings
from app.models.registry import get_meta
from ..base import AlgorithmAdapter
from . import get_device

class TsCanAdapter(AlgorithmAdapter):
    id = "TS-CAN"
    def __init__(self):
        self.device = get_device()
        self.model = TSCAN(frame_depth=20, img_size=72).to(self.device)
        weight_path = settings.weights_dir / get_meta(self.id).weight_filename
        state = torch.load(weight_path, map_location=self.device)
        self.model.load_state_dict({k.replace("module.",""): v for k,v in state.items()})
        self.model.eval()

    @torch.inference_mode()
    def estimate_bvp(self, rgb_signal, frames, fs):
        # frames: (T,H,W,3) uint8 → resize 72x72, normalize, build appearance+motion streams
        import cv2
        T = len(frames)
        crops = np.stack([cv2.resize(f, (72,72)) for f in frames]).astype(np.float32)
        crops /= 255.0
        motion = np.zeros_like(crops)
        motion[1:] = (crops[1:] - crops[:-1]) / (crops[1:] + crops[:-1] + 1e-7)
        motion = (motion - motion.mean()) / (motion.std() + 1e-7)
        app = (crops - crops.mean()) / (crops.std() + 1e-7)
        tensor = lambda x: torch.from_numpy(x).permute(0,3,1,2).to(self.device)
        bvp = self.model(tensor(motion), tensor(app)).cpu().numpy().squeeze()
        return bvp
```

- [ ] **Step 3: 테스트 — weight 없으면 skip**
```python
import pytest, numpy as np
from pathlib import Path
from app.core.config import settings

@pytest.mark.skipif(not (settings.weights_dir / "UBFC-rPPG_TSCAN.pth").exists(),
                    reason="weight not downloaded")
def test_tscan_runs():
    from app.pipeline.algorithms.supervised.ts_can import TsCanAdapter
    frames = (np.random.rand(120, 96, 96, 3) * 255).astype(np.uint8)
    bvp = TsCanAdapter().estimate_bvp(None, frames, 30)
    assert len(bvp) == 120
```

- [ ] **Step 4: EfficientPhys 동일 패턴**

- [ ] **Step 5: 커밋**
```bash
git commit -am "feat(algorithms): TS-CAN and EfficientPhys supervised adapters"
```

### Task 5.4: Supervised adapters — PhysFormer, RhythmFormer

같은 패턴, 입력 텐서 형식만 모델별로 조정. 각 모델 시그니처는 `rppg_toolbox/neural_methods/model/{PhysFormer,RhythmFormer}.py` 참조.

- [ ] **Step 1~5:** 어댑터 작성 + skip-기반 테스트 + commit
```bash
git commit -am "feat(algorithms): PhysFormer and RhythmFormer adapters"
```

### Task 5.5: BigSmall 어댑터 (호흡수 추출 포함)

**Files:** `backend/app/pipeline/algorithms/supervised/bigsmall.py`, test

- [ ] **Step 1~5:** BigSmall은 출력이 multi-head (BVP, RR, AU). BVP 외에 RR을 `extras={"respiration_rpm": ...}`로 반환
```bash
git commit -am "feat(algorithms): BigSmall multitask adapter (BVP + respiration)"
```

---

## Phase 6 — 오케스트레이터 + Consensus

### Task 6.1: 알고리즘 병렬 실행

**Files:** `backend/app/pipeline/orchestrator.py`, `backend/tests/test_orchestrator.py`

- [ ] **Step 1: 실패 테스트 — 합성 영상 1개로 8개 결과 길이 확인 (deep adapter는 weight 없을 시 skip)**

- [ ] **Step 2~5:** 구현
```python
# orchestrator.py
import asyncio
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from app.models.registry import ALGORITHMS, get_meta
from app.pipeline.preprocess.frame_decoder import decode_video
from app.pipeline.preprocess.face_roi import extract_roi_signal
from app.pipeline.preprocess.quality_gate import assess
from app.pipeline.hrv.peak_detect import bvp_to_ibi
from app.pipeline.hrv.time_domain import time_domain_hrv
from app.pipeline.hrv.freq_domain import freq_domain_hrv
from app.pipeline.hrv.nonlinear import poincare
from app.pipeline.stress.baevsky import baevsky_si
from app.pipeline.stress.composite import composite_stress, composite_level
from app.pipeline.reliability.snr import bvp_snr_db
from app.pipeline.reliability.scoring import reliability_score, reliability_grade

UNSUP_IDS = {"POS","CHROM","OMIT"}

def _build_adapter(algo_id: str):
    # 동적 로딩 (process pool에서 안전)
    if algo_id == "POS": from app.pipeline.algorithms.unsupervised.pos import PosAdapter; return PosAdapter()
    if algo_id == "CHROM": from app.pipeline.algorithms.unsupervised.chrom import ChromAdapter; return ChromAdapter()
    if algo_id == "OMIT": from app.pipeline.algorithms.unsupervised.omit import OmitAdapter; return OmitAdapter()
    if algo_id == "TS-CAN": from app.pipeline.algorithms.supervised.ts_can import TsCanAdapter; return TsCanAdapter()
    if algo_id == "EfficientPhys": from app.pipeline.algorithms.supervised.efficientphys import EfficientPhysAdapter; return EfficientPhysAdapter()
    if algo_id == "PhysFormer": from app.pipeline.algorithms.supervised.physformer import PhysFormerAdapter; return PhysFormerAdapter()
    if algo_id == "RhythmFormer": from app.pipeline.algorithms.supervised.rhythmformer import RhythmFormerAdapter; return RhythmFormerAdapter()
    if algo_id == "BigSmall": from app.pipeline.algorithms.supervised.bigsmall import BigSmallAdapter; return BigSmallAdapter()
    raise KeyError(algo_id)

def _run_one(algo_id, rgb_signal, frames, fs):
    import time
    t0 = time.perf_counter()
    bvp = _build_adapter(algo_id).estimate_bvp(rgb_signal, frames, fs)
    return algo_id, bvp, (time.perf_counter() - t0) * 1000

async def run_pipeline(video_path, algorithm_ids: list[str], progress_cb=None):
    frames, fs, res = decode_video(video_path)
    if progress_cb: await progress_cb(0.2, "face_roi")
    rgb_signal, detected = extract_roi_signal(frames)
    quality = assess(frames, detected)
    if progress_cb: await progress_cb(0.4, "algorithms")

    loop = asyncio.get_running_loop()
    results: dict[str, tuple[np.ndarray, float]] = {}

    # Unsupervised in ProcessPoolExecutor (CPU bound, picklable)
    with ProcessPoolExecutor(max_workers=3) as pool:
        unsup_futs = [
            loop.run_in_executor(pool, _run_one, aid, rgb_signal, None, fs)
            for aid in algorithm_ids if aid in UNSUP_IDS
        ]
        for fut in asyncio.as_completed(unsup_futs):
            aid, bvp, ms = await fut
            results[aid] = (bvp, ms)
            if progress_cb: await progress_cb(0.4 + 0.05 * len(results), f"done:{aid}")

    # Supervised sequentially (MPS는 단일 디바이스)
    for aid in algorithm_ids:
        if aid in UNSUP_IDS: continue
        try:
            aid2, bvp, ms = _run_one(aid, rgb_signal, frames, fs)
            results[aid2] = (bvp, ms)
        except FileNotFoundError:
            continue  # weight missing → skip
        if progress_cb: await progress_cb(0.4 + 0.05 * len(results), f"done:{aid}")

    # Aggregate per-algorithm metrics
    hr_values = []
    per_algo = []
    for aid, (bvp, ms) in results.items():
        ibi = bvp_to_ibi(bvp, fs)
        td = time_domain_hrv(ibi)
        fd = freq_domain_hrv(ibi)
        pc = poincare(ibi)
        bv = baevsky_si(ibi)
        comp = composite_stress(bv.si, fd.lf_hf_ratio, td.rmssd_ms)
        snr = bvp_snr_db(bvp, fs)
        per_algo.append((aid, bvp, ms, td, fd, pc, bv, comp, snr))
        if td.hr_bpm > 0: hr_values.append(td.hr_bpm)
    median_hr = float(np.median(hr_values)) if hr_values else 0.0

    final = []
    for aid, bvp, ms, td, fd, pc, bv, comp, snr in per_algo:
        rel = reliability_score(snr_db=snr, tracking=quality.detected_ratio,
                                motion_px=quality.mean_motion_px,
                                hr_dev=td.hr_bpm - median_hr)
        final.append(dict(
            id=aid, bvp=bvp, compute_ms=ms,
            hrv=dict(hr_bpm=td.hr_bpm, ibi_mean_ms=td.ibi_mean_ms,
                     sdnn_ms=td.sdnn_ms, rmssd_ms=td.rmssd_ms, pnn50_pct=td.pnn50_pct,
                     lf_power=fd.lf_power, hf_power=fd.hf_power, lf_hf_ratio=fd.lf_hf_ratio,
                     sd1=pc.sd1, sd2=pc.sd2),
            stress=dict(baevsky_si=bv.si, baevsky_level=bv.level,
                        composite_score=comp, composite_level=composite_level(comp)),
            reliability=dict(score=rel, grade=reliability_grade(rel),
                             components=dict(snr_db=snr,
                                             face_tracking_pct=quality.detected_ratio*100,
                                             deviation_from_consensus=td.hr_bpm - median_hr,
                                             motion_penalty=quality.mean_motion_px))
        ))
    return dict(algorithms=final, quality=quality, video_meta=dict(duration_s=len(frames)/fs, fps=fs, resolution=res))
```
commit: `feat(pipeline): orchestrator with parallel algorithm execution`

### Task 6.2: Consensus aggregator

**Files:** `backend/app/pipeline/consensus.py`, test

- [ ] **Step 1: 실패 테스트**
```python
from app.pipeline.consensus import build_consensus

def test_weighted_median_skips_low_reliability():
    algos = [
        dict(id="A", hrv=dict(hr_bpm=70, rmssd_ms=30, lf_hf_ratio=1.5),
             stress=dict(baevsky_si=200, composite_score=40), reliability=dict(score=80)),
        dict(id="B", hrv=dict(hr_bpm=72, rmssd_ms=32, lf_hf_ratio=1.6),
             stress=dict(baevsky_si=210, composite_score=42), reliability=dict(score=70)),
        dict(id="C", hrv=dict(hr_bpm=120, rmssd_ms=5, lf_hf_ratio=8),
             stress=dict(baevsky_si=1200, composite_score=95), reliability=dict(score=20)),  # low → 제외
    ]
    c = build_consensus(algos)
    assert 70 <= c["hr_bpm"] <= 72
    assert c["contributing_algorithms"] == 2
```

- [ ] **Step 2~5: 구현**
```python
# consensus.py
import numpy as np

def _weighted_median(values, weights):
    pairs = sorted(zip(values, weights))
    cum, half = 0.0, sum(weights) / 2
    for v, w in pairs:
        cum += w
        if cum >= half: return v
    return pairs[-1][0]

def build_consensus(algos: list[dict]) -> dict | None:
    weights = [max(a["reliability"]["score"] - 30, 0) for a in algos]
    if sum(weights) <= 0: return None
    contributing = sum(1 for w in weights if w > 0)
    def wmed(key_path):
        keys = key_path.split(".")
        vals = []
        ws = []
        for a, w in zip(algos, weights):
            if w <= 0: continue
            v = a
            for k in keys: v = v[k]
            vals.append(v); ws.append(w)
        return _weighted_median(vals, ws)
    score = wmed("stress.composite_score")
    return dict(
        stress_score=score,
        stress_level=("low" if score<30 else "mid" if score<60 else "high" if score<80 else "very_high"),
        hr_bpm=wmed("hrv.hr_bpm"),
        rmssd_ms=wmed("hrv.rmssd_ms"),
        lf_hf_ratio=wmed("hrv.lf_hf_ratio"),
        baevsky_si=wmed("stress.baevsky_si"),
        reliability=dict(
            score=float(np.average([a["reliability"]["score"] for a,w in zip(algos,weights) if w>0],
                                   weights=[w for w in weights if w>0])),
            grade="high",  # 후처리에서 grade 보정
            components={},
        ),
        contributing_algorithms=contributing,
    )
```
commit: `feat(pipeline): reliability-weighted consensus`

---

## Phase 7 — API 라우터

### Task 7.1: Pydantic schemas

**Files:** `backend/app/schemas/{measurement,algorithm}.py`, test

- [ ] **Step 1~5:** Pydantic v2 모델 (스펙 §5.1과 동형). camelCase alias로 직렬화.
```python
# schemas/measurement.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

def camel(s: str): parts = s.split("_"); return parts[0] + "".join(w.title() for w in parts[1:])
class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=camel, populate_by_name=True)

class HRVMetrics(CamelModel):
    hr_bpm: float; ibi_mean_ms: float; sdnn_ms: float; rmssd_ms: float; pnn50_pct: float
    lf_power: float; hf_power: float; lf_hf_ratio: float; sd1: float; sd2: float

class StressIndices(CamelModel):
    baevsky_si: float; baevsky_level: Literal["normal","mild","moderate","high"]
    lf_hf_stress: float = 0.0
    composite_score: float; composite_level: Literal["low","mid","high","very_high"]

class ReliabilityComponents(CamelModel):
    snr_db: float; face_tracking_pct: float
    deviation_from_consensus: float; motion_penalty: float

class Reliability(CamelModel):
    score: float; grade: Literal["low","medium","high"]
    components: ReliabilityComponents

class AlgorithmMetaOut(CamelModel):
    id: str; display_name: str; short_description: str
    type: Literal["unsupervised","supervised"]; backbone: str
    pretrained_on: str | None = None; model_size_mb: int | None = None

class AlgorithmResult(CamelModel):
    meta: AlgorithmMetaOut
    hrv: HRVMetrics; stress: StressIndices; reliability: Reliability
    bvp_sparkline: list[float]
    extras: dict | None = None
    compute_ms: float

class ConsensusResult(CamelModel):
    stress_score: float; stress_level: Literal["low","mid","high","very_high"]
    hr_bpm: float; rmssd_ms: float; lf_hf_ratio: float; baevsky_si: float
    reliability: Reliability
    contributing_algorithms: int

class VideoMeta(CamelModel):
    duration_s: float; fps: float; resolution: tuple[int, int]

class MeasurementResponse(CamelModel):
    job_id: str
    status: Literal["queued","processing","done","failed"]
    progress: float
    video_meta: VideoMeta | None = None
    consensus: ConsensusResult | None = None
    algorithms: list[AlgorithmResult] | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Not a medical device. Educational/research use only."
```
commit: `feat(schemas): measurement and algorithm pydantic models`

### Task 7.2: Job store (in-memory)

**Files:** `backend/app/core/jobs.py`, test

- [ ] **Step 1~5:** 단일 사용자 in-memory dict + asyncio.Lock + TTL 정리
```python
# core/jobs.py
import asyncio, uuid, time
from dataclasses import dataclass, field

@dataclass
class Job:
    id: str
    status: str = "queued"
    progress: float = 0.0
    stage: str = ""
    created_at: float = field(default_factory=time.time)
    result: dict | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

class JobStore:
    def __init__(self): self._jobs: dict[str, Job] = {}; self._lock = asyncio.Lock()
    async def create(self) -> Job:
        async with self._lock:
            j = Job(id=uuid.uuid4().hex); self._jobs[j.id] = j; return j
    def get(self, jid): return self._jobs.get(jid)
    async def update(self, jid, **kwargs):
        async with self._lock:
            j = self._jobs.get(jid)
            if j: [setattr(j, k, v) for k, v in kwargs.items()]
    async def cleanup(self, ttl=3600):
        now = time.time()
        async with self._lock:
            for k in list(self._jobs):
                if now - self._jobs[k].created_at > ttl: del self._jobs[k]

store = JobStore()
```
commit: `feat(core): in-memory job store`

### Task 7.3: SSE event broker

**Files:** `backend/app/core/events.py`

- [ ] **Step 1~5:** job_id별 asyncio.Queue 발행/구독
```python
# core/events.py
import asyncio
from collections import defaultdict

class EventBus:
    def __init__(self): self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)
    def subscribe(self, jid):
        q = asyncio.Queue(); self._queues[jid].append(q); return q
    def unsubscribe(self, jid, q):
        if q in self._queues[jid]: self._queues[jid].remove(q)
    async def publish(self, jid, event: dict):
        for q in list(self._queues[jid]): await q.put(event)
    async def close(self, jid):
        await self.publish(jid, {"event": "close"})

bus = EventBus()
```
commit: `feat(core): SSE event bus`

### Task 7.4: `/api/v1/measurements` 라우터

**Files:** `backend/app/api/v1/measurements.py`, test

- [ ] **Step 1~5:** POST/GET/DELETE/stream
```python
# api/v1/measurements.py
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from sse_starlette.sse import EventSourceResponse
from pathlib import Path
import json
from app.core.config import settings
from app.core.jobs import store
from app.core.events import bus
from app.pipeline.orchestrator import run_pipeline
from app.pipeline.consensus import build_consensus
from app.schemas.measurement import MeasurementResponse

router = APIRouter(prefix="/measurements", tags=["measurements"])

async def _process(job_id: str, path: Path, algorithm_ids: list[str]):
    await store.update(job_id, status="processing", progress=0.05, stage="decoding")
    async def progress(p, stage):
        await store.update(job_id, progress=p, stage=stage)
        await bus.publish(job_id, dict(event="progress", progress=p, stage=stage))
    try:
        out = await run_pipeline(path, algorithm_ids, progress)
        consensus = build_consensus(out["algorithms"])
        await store.update(job_id, status="done", progress=1.0, stage="done",
                           result=dict(algorithms=out["algorithms"],
                                       consensus=consensus,
                                       video_meta=out["video_meta"]),
                           warnings=out["quality"].warnings)
        await bus.publish(job_id, dict(event="done"))
    except Exception as e:
        await store.update(job_id, status="failed", error=str(e))
        await bus.publish(job_id, dict(event="failed", error=str(e)))
    finally:
        try: path.unlink(missing_ok=True)
        except Exception: pass

@router.post("", status_code=202)
async def create_measurement(bg: BackgroundTasks,
                             video: UploadFile = File(...),
                             algorithms: str | None = None):
    if video.size and video.size > settings.max_video_mb * 1024 * 1024:
        raise HTTPException(413, "video too large")
    job = await store.create()
    target = settings.tmp_dir / f"{job.id}_{video.filename}"
    target.write_bytes(await video.read())
    ids = [a.strip() for a in algorithms.split(",")] if algorithms else \
          ["POS","CHROM","OMIT","TS-CAN","EfficientPhys","PhysFormer","RhythmFormer","BigSmall"]
    bg.add_task(_process, job.id, target, ids)
    return {"jobId": job.id, "status": "queued"}

@router.get("/{job_id}", response_model=MeasurementResponse, response_model_by_alias=True)
async def get_measurement(job_id: str):
    j = store.get(job_id)
    if not j: raise HTTPException(404)
    payload = dict(job_id=j.id, status=j.status, progress=j.progress, warnings=j.warnings)
    if j.result:
        payload.update(video_meta=j.result["video_meta"],
                       consensus=j.result["consensus"],
                       algorithms=j.result["algorithms"])
    return payload

@router.get("/{job_id}/stream")
async def stream(job_id: str):
    if not store.get(job_id): raise HTTPException(404)
    queue = bus.subscribe(job_id)
    async def gen():
        try:
            while True:
                ev = await queue.get()
                yield {"event": ev.get("event","message"), "data": json.dumps(ev)}
                if ev.get("event") in {"done","failed","close"}: break
        finally:
            bus.unsubscribe(job_id, queue)
    return EventSourceResponse(gen())

@router.delete("/{job_id}", status_code=204)
async def delete_measurement(job_id: str):
    j = store.get(job_id)
    if j: del store._jobs[job_id]
```
commit: `feat(api): /measurements POST/GET/DELETE/stream endpoints`

### Task 7.5: `/algorithms`, `/health`, main app

**Files:** `backend/app/api/v1/{algorithms,health}.py`, `backend/app/main.py`

- [ ] **Step 1~5:**
```python
# api/v1/algorithms.py
from fastapi import APIRouter
from app.models.registry import ALGORITHMS
router = APIRouter(prefix="/algorithms", tags=["algorithms"])
@router.get("")
async def list_algorithms(): return [a.__dict__ for a in ALGORITHMS]
```
```python
# api/v1/health.py
from fastapi import APIRouter
import torch
from app.core.config import settings
from app.models.registry import ALGORITHMS
router = APIRouter(prefix="/health", tags=["health"])
@router.get("")
async def health():
    loaded = [a.id for a in ALGORITHMS if a.weight_filename and (settings.weights_dir / a.weight_filename).exists()]
    return {"status":"ok","mpsAvailable":torch.backends.mps.is_available(),"weightsLoaded":loaded}
```
```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import measurements, algorithms, health

app = FastAPI(title="rPPG Stress Demo API")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(measurements.router, prefix="/api/v1")
app.include_router(algorithms.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
```

- [ ] **Step 6: 통합 테스트 (httpx)**
```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app
def test_health():
    c = TestClient(app)
    assert c.get("/api/v1/health").status_code == 200
def test_algorithms_list():
    c = TestClient(app)
    r = c.get("/api/v1/algorithms")
    assert r.status_code == 200 and len(r.json()) == 8
```

- [ ] **Step 7: 커밋**
```bash
git commit -am "feat(api): health, algorithms list, app entrypoint with CORS"
```

---

## Phase 8 — 가중치 다운로더

### Task 8.1: `scripts/download_weights.py`

**Files:** `backend/scripts/download_weights.py`

- [ ] **Step 1~5:** registry 순회 + httpx로 streaming download + sha256 검증 skip(없으면 size 확인)
```python
# scripts/download_weights.py
import sys, httpx
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.config import settings
from app.models.registry import ALGORITHMS

def main():
    for a in ALGORITHMS:
        if not a.weight_url: continue
        target = settings.weights_dir / a.weight_filename
        if target.exists():
            print(f"✓ {a.id} already present"); continue
        print(f"↓ {a.id} ← {a.weight_url}")
        with httpx.stream("GET", a.weight_url, follow_redirects=True) as r:
            r.raise_for_status()
            with open(target, "wb") as f:
                for chunk in r.iter_bytes(): f.write(chunk)
        print(f"✓ saved {target.stat().st_size//1024} KB")

if __name__ == "__main__": main()
```

- [ ] **Step 6: 실행 + 확인**
```bash
cd backend && uv run python scripts/download_weights.py
ls -lh weights/
```

- [ ] **Step 7: 커밋**
```bash
git add backend/scripts/download_weights.py
git commit -m "feat(scripts): weight downloader for 5 supervised models"
```

---

## Phase 9 — 프론트엔드 골격 (entities, shared)

### Task 9.1: `shared/api/client.ts` + `shared/api/measurements.ts`

- [ ] **Step 1~5:**
```ts
// shared/api/client.ts
const BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api/v1';
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
export function streamUrl(path: string) { return `${BASE}${path}`; }
```
```ts
// shared/api/measurements.ts
import { api } from './client';
import type { MeasurementResponse, AlgorithmMeta } from '@entities/measurement';

export async function uploadVideo(file: File): Promise<{ jobId: string }> {
  const fd = new FormData(); fd.append('video', file);
  return api('/measurements', { method: 'POST', body: fd });
}
export const getMeasurement = (jobId: string) =>
  api<MeasurementResponse>(`/measurements/${jobId}`);
export const listAlgorithms = () => api<AlgorithmMeta[]>('/algorithms');
```
commit: `feat(shared/api): client and measurements endpoints`

### Task 9.2: `entities/measurement/model/types.ts`

- [ ] **Step 1~5:** 스펙 §5.1 TS interface 그대로 작성. (이미 design doc에 전체 코드 있음)
commit: `feat(entities/measurement): TS types matching backend schemas`

### Task 9.3: `entities/algorithm/model/registry.ts` (frontend mirror)

- [ ] **Step 1~5:** 8개 알고리즘 메타를 백엔드와 동일하게 (런타임에 `/algorithms`로 fetch도 가능하지만, 카드 placeholder를 SSR 없이 즉시 채우려면 mirror가 편함)
commit: `feat(entities/algorithm): frontend algorithm metadata mirror`

### Task 9.4: `app/providers/QueryProvider.tsx`, `App.tsx`

- [ ] **Step 1~5:**
```tsx
// app/providers/QueryProvider.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { PropsWithChildren } from 'react';
const client = new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, retry: 1 } } });
export const QueryProvider = ({ children }: PropsWithChildren) =>
  <QueryClientProvider client={client}>{children}</QueryClientProvider>;
```
```tsx
// app/App.tsx
import { QueryProvider } from './providers/QueryProvider';
import { MeasurePage } from '@pages/measure/MeasurePage';
import '@app/styles/global.css';
export const App = () => <QueryProvider><MeasurePage /></QueryProvider>;
```
commit: `feat(app): query provider and root component`

---

## Phase 10 — Features

### Task 10.1: `features/upload-video`

**Files:** `features/upload-video/ui/UploadDropzone.tsx`, `model/useUpload.ts`

- [ ] **Step 1~5:**
```tsx
// ui/UploadDropzone.tsx
import { useDropzone } from 'react-dropzone';
import { useUpload } from '../model/useUpload';

export function UploadDropzone() {
  const { mutate, isPending, error } = useUpload();
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'video/mp4': ['.mp4'], 'video/webm': ['.webm'], 'video/quicktime': ['.mov'] },
    maxFiles: 1,
    onDrop: (files) => files[0] && mutate(files[0]),
  });
  return (
    <div {...getRootProps()} className="border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer hover:border-neutral-400">
      <input {...getInputProps()} />
      {isPending ? <p>업로드 중…</p>
        : isDragActive ? <p>여기에 놓으세요</p>
        : <p>mp4/webm 영상을 끌어다 놓으세요 (10~120초)</p>}
      {error && <p className="text-red-600 mt-2">{error.message}</p>}
    </div>
  );
}
```
```ts
// model/useUpload.ts
import { useMutation } from '@tanstack/react-query';
import { uploadVideo } from '@shared/api/measurements';
import { useMeasurementStore } from '@features/run-measurement/model/measurementStore';

export function useUpload() {
  const setJob = useMeasurementStore(s => s.setJobId);
  return useMutation({
    mutationFn: uploadVideo,
    onSuccess: (data) => setJob(data.jobId),
  });
}
```
commit: `feat(features/upload-video): dropzone and upload mutation`

### Task 10.2: `features/run-measurement` (zustand + SSE)

**Files:** `model/measurementStore.ts`, `model/useMeasurement.ts`

- [ ] **Step 1~5:**
```ts
// model/measurementStore.ts
import { create } from 'zustand';
interface S { jobId: string | null; setJobId(id: string|null): void; }
export const useMeasurementStore = create<S>(set => ({
  jobId: null, setJobId: (id) => set({ jobId: id }),
}));
```
```ts
// model/useMeasurement.ts
import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';
import { getMeasurement } from '@shared/api/measurements';
import { streamUrl } from '@shared/api/client';
import { useMeasurementStore } from './measurementStore';

export function useMeasurement() {
  const jobId = useMeasurementStore(s => s.jobId);
  const q = useQuery({
    queryKey: ['measurement', jobId],
    queryFn: () => getMeasurement(jobId!),
    enabled: !!jobId,
    refetchInterval: (d) => (d.state.data?.status === 'done' || d.state.data?.status === 'failed' ? false : 1500),
  });

  useEffect(() => {
    if (!jobId) return;
    const es = new EventSource(streamUrl(`/measurements/${jobId}/stream`));
    es.addEventListener('done', () => q.refetch());
    es.addEventListener('failed', () => q.refetch());
    return () => es.close();
  }, [jobId]);

  return q;
}
```
commit: `feat(features/run-measurement): zustand job store + SSE-aware query`

### Task 10.3: `features/algorithm-result-card`

**Files:** `ui/AlgorithmResultCard.tsx`, `ui/ReliabilityBadge.tsx`, `ui/BvpSparkline.tsx`, `ui/MetricRow.tsx`

- [ ] **Step 1~5:**
```tsx
// ui/AlgorithmResultCard.tsx
import type { AlgorithmResult } from '@entities/measurement';
import { ReliabilityBadge } from './ReliabilityBadge';
import { BvpSparkline } from './BvpSparkline';
import { MetricRow } from './MetricRow';

export function AlgorithmResultCard({ result }: { result: AlgorithmResult }) {
  const { meta, hrv, stress, reliability, bvpSparkline, extras } = result;
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm flex flex-col gap-3">
      <header className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-base">{meta.displayName}</h3>
          <p className="text-xs text-neutral-500">{meta.shortDescription}</p>
          <p className="text-[10px] text-neutral-400 mt-1">
            {meta.type === 'supervised' ? `trained on ${meta.pretrainedOn}` : 'signal processing'}
          </p>
        </div>
        <ReliabilityBadge grade={reliability.grade} score={reliability.score} />
      </header>

      <BvpSparkline data={bvpSparkline} />

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        <MetricRow label="HR" value={`${hrv.hrBpm.toFixed(0)} BPM`} />
        <MetricRow label="RMSSD" value={`${hrv.rmssdMs.toFixed(0)} ms`} />
        <MetricRow label="LF/HF" value={hrv.lfHfRatio.toFixed(2)} />
        <MetricRow label="Baev SI" value={stress.baevskySi.toFixed(0)} />
        <MetricRow label="Stress" value={`${stress.compositeScore.toFixed(0)} (${stress.compositeLevel})`} highlight />
        {extras?.respirationRpm && <MetricRow label="호흡" value={`${extras.respirationRpm.toFixed(0)} /min`} />}
      </div>
    </div>
  );
}
```
```tsx
// ui/ReliabilityBadge.tsx
const STYLES = { high: 'bg-emerald-100 text-emerald-700', medium: 'bg-amber-100 text-amber-700', low: 'bg-rose-100 text-rose-700' };
export function ReliabilityBadge({ grade, score }: { grade: 'low'|'medium'|'high'; score: number }) {
  return <span className={`text-xs px-2 py-1 rounded-full font-medium ${STYLES[grade]}`}>{grade.toUpperCase()} {score.toFixed(0)}</span>;
}
```
```tsx
// ui/BvpSparkline.tsx
import { LineChart, Line, ResponsiveContainer } from 'recharts';
export function BvpSparkline({ data }: { data: number[] }) {
  const points = data.map((v, i) => ({ i, v }));
  return (
    <div className="h-12">
      <ResponsiveContainer><LineChart data={points}><Line type="monotone" dataKey="v" stroke="#0ea5e9" strokeWidth={1.5} dot={false} /></LineChart></ResponsiveContainer>
    </div>
  );
}
```
```tsx
// ui/MetricRow.tsx
export function MetricRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex justify-between items-baseline">
      <span className="text-neutral-500">{label}</span>
      <span className={highlight ? 'font-semibold text-neutral-900' : 'text-neutral-800'}>{value}</span>
    </div>
  );
}
```
commit: `feat(features/algorithm-result-card): card with sparkline, metrics, reliability badge`

---

## Phase 11 — Widgets + Pages

### Task 11.1: `widgets/consensus-dashboard`

**Files:** `ui/ConsensusDashboard.tsx`, `ui/StressGauge.tsx`, `ui/HRVQuickStats.tsx`

- [ ] **Step 1~5:**
```tsx
// ui/StressGauge.tsx — Recharts RadialBar
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts';
export function StressGauge({ score, level }: { score: number; level: string }) {
  const color = score < 30 ? '#10b981' : score < 60 ? '#f59e0b' : score < 80 ? '#ef4444' : '#7c1d1d';
  return (
    <div className="relative h-40 w-40">
      <ResponsiveContainer>
        <RadialBarChart innerRadius="70%" outerRadius="100%" startAngle={90} endAngle={-270} data={[{ name:'s', value:score, fill:color }]}>
          <RadialBar background dataKey="value" />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold">{score.toFixed(0)}</span>
        <span className="text-xs uppercase text-neutral-500">{level}</span>
      </div>
    </div>
  );
}
```
```tsx
// ui/ConsensusDashboard.tsx
import type { ConsensusResult } from '@entities/measurement';
import { StressGauge } from './StressGauge';
import { ReliabilityBadge } from '@features/algorithm-result-card/ui/ReliabilityBadge';

export function ConsensusDashboard({ data }: { data: ConsensusResult }) {
  return (
    <section className="rounded-3xl bg-white border p-6 flex flex-wrap items-center gap-6">
      <StressGauge score={data.stressScore} level={data.stressLevel} />
      <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
        <div><span className="text-neutral-500">HR</span> <span className="font-semibold">{data.hrBpm.toFixed(0)} BPM</span></div>
        <div><span className="text-neutral-500">RMSSD</span> <span className="font-semibold">{data.rmssdMs.toFixed(0)} ms</span></div>
        <div><span className="text-neutral-500">LF/HF</span> <span className="font-semibold">{data.lfHfRatio.toFixed(2)}</span></div>
        <div><span className="text-neutral-500">Baevsky SI</span> <span className="font-semibold">{data.baevskySi.toFixed(0)}</span></div>
      </div>
      <div className="ml-auto flex flex-col items-end gap-1">
        <ReliabilityBadge grade={data.reliability.grade} score={data.reliability.score} />
        <span className="text-xs text-neutral-500">{data.contributingAlgorithms} / 8 algorithms</span>
      </div>
    </section>
  );
}
```
commit: `feat(widgets/consensus-dashboard): stress gauge + quick HRV stats`

### Task 11.2: `widgets/algorithm-cards-grid`

```tsx
// ui/AlgorithmCardsGrid.tsx
import type { AlgorithmResult } from '@entities/measurement';
import { AlgorithmResultCard } from '@features/algorithm-result-card/ui/AlgorithmResultCard';

export function AlgorithmCardsGrid({ results }: { results: AlgorithmResult[] }) {
  const sorted = [...results].sort((a,b) => b.reliability.score - a.reliability.score);
  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {sorted.map(r => <AlgorithmResultCard key={r.meta.id} result={r} />)}
    </section>
  );
}
```
commit: `feat(widgets/algorithm-cards-grid): reliability-sorted 4x2 grid`

### Task 11.3: `widgets/measurement-progress`

```tsx
// ui/MeasurementProgress.tsx
export function MeasurementProgress({ progress, stage }: { progress: number; stage: string }) {
  return (
    <div className="rounded-2xl bg-white border p-6 flex flex-col gap-2">
      <div className="flex justify-between text-sm"><span>{stage || '대기 중'}</span><span>{(progress*100).toFixed(0)}%</span></div>
      <div className="h-2 bg-neutral-200 rounded-full overflow-hidden">
        <div className="h-full bg-sky-500 transition-all" style={{ width: `${progress*100}%` }} />
      </div>
    </div>
  );
}
```
commit: `feat(widgets/measurement-progress): progress bar`

### Task 11.4: `pages/measure/MeasurePage.tsx`

```tsx
import { UploadDropzone } from '@features/upload-video/ui/UploadDropzone';
import { useMeasurement } from '@features/run-measurement/model/useMeasurement';
import { ConsensusDashboard } from '@widgets/consensus-dashboard/ui/ConsensusDashboard';
import { AlgorithmCardsGrid } from '@widgets/algorithm-cards-grid/ui/AlgorithmCardsGrid';
import { MeasurementProgress } from '@widgets/measurement-progress/ui/MeasurementProgress';

export function MeasurePage() {
  const { data } = useMeasurement();
  return (
    <main className="max-w-6xl mx-auto p-6 flex flex-col gap-6">
      <header><h1 className="text-2xl font-bold">rPPG Stress Demo</h1></header>
      <UploadDropzone />
      {data && data.status !== 'done' && <MeasurementProgress progress={data.progress} stage={(data as any).stage ?? ''} />}
      {data?.consensus && <ConsensusDashboard data={data.consensus} />}
      {data?.algorithms && <AlgorithmCardsGrid results={data.algorithms} />}
      {data?.warnings?.length ? (
        <ul className="text-sm text-amber-700 list-disc list-inside">{data.warnings.map(w => <li key={w}>{w}</li>)}</ul>
      ) : null}
      <footer className="text-xs text-neutral-500 border-t pt-4">⚠ Not a medical device. Educational/research use only.</footer>
    </main>
  );
}
```
commit: `feat(pages/measure): wire upload + progress + dashboard + cards`

### Task 11.5: 수동 검증 (브라우저)

- [ ] **Step 1: 백엔드 기동**
```bash
cd backend && PYTORCH_ENABLE_MPS_FALLBACK=1 uv run uvicorn app.main:app --reload --port 8000
```
- [ ] **Step 2: 프론트엔드 기동**
```bash
cd frontend && pnpm dev
```
- [ ] **Step 3: 브라우저에서 `http://localhost:5173` 접속 → 샘플 mp4 업로드 → 8개 카드 표시 확인**
- [ ] **Step 4: 콘솔 에러 없음 확인**

---

## Phase 12 — 회귀 + E2E

### Task 12.1: 회귀 테스트 (UBFC-rPPG subject1)

**Files:** `backend/tests/test_regression_ubfc.py`, `backend/tests/fixtures/ubfc_subject1.mp4`, `backend/tests/fixtures/ubfc_subject1_expected.json`

- [ ] **Step 1: UBFC-rPPG subject1 영상 1개 + GT HR 값 fixture로 추가 (gitignore 처리)**

- [ ] **Step 2: 테스트**
```python
import json, pytest, asyncio
from pathlib import Path
from app.pipeline.orchestrator import run_pipeline

@pytest.mark.regression
def test_ubfc_subject1_hr_within_3bpm():
    expected = json.loads(Path("tests/fixtures/ubfc_subject1_expected.json").read_text())
    out = asyncio.run(run_pipeline(Path("tests/fixtures/ubfc_subject1.mp4"), ["POS","CHROM","OMIT"]))
    pos_hr = next(a["hrv"]["hr_bpm"] for a in out["algorithms"] if a["id"] == "POS")
    assert abs(pos_hr - expected["hr_bpm"]) <= 3
```

- [ ] **Step 3: commit**
```bash
git commit -am "test(regression): UBFC-rPPG subject1 HR sanity"
```

### Task 12.2: Playwright E2E

**Files:** `frontend/e2e/measure.spec.ts`, `frontend/playwright.config.ts`

- [ ] **Step 1: playwright init**
```bash
cd frontend && pnpm dlx playwright install --with-deps chromium
```
- [ ] **Step 2:**
```ts
// e2e/measure.spec.ts
import { test, expect } from '@playwright/test';
test('upload → dashboard + 8 cards', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await page.setInputFiles('input[type=file]', 'tests/fixtures/sample_30s.mp4');
  await expect(page.locator('section').filter({ hasText: 'STRESS' })).toBeVisible({ timeout: 60_000 });
  await expect(page.locator('[data-testid=algorithm-card]')).toHaveCount(8);
});
```
- [ ] **Step 3: commit**
```bash
git commit -am "test(e2e): upload + dashboard + 8 cards playwright test"
```

---

## 완료 체크리스트

- [ ] backend uv lock + `uv run pytest` 전부 green
- [ ] `uv run uvicorn app.main:app` 정상 기동, `/api/v1/health`에서 `mpsAvailable: true`, `weightsLoaded: 5` 확인
- [ ] frontend `pnpm dev` 기동, 샘플 영상 업로드 → 대시보드 + 8개 카드 렌더
- [ ] UBFC subject1 회귀 테스트 PASS
- [ ] Playwright E2E PASS
- [ ] 모든 phase commit 완료, working tree clean
