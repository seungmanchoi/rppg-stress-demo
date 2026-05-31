import { ALGORITHM_DEFAULTS } from '@entities/algorithm/model/registry';
import type { AlgorithmResult } from '@entities/measurement';
import { RecordPanel } from '@features/record-video';
import { useMeasurement } from '@features/run-measurement/model/useMeasurement';
import { useMeasurementStore } from '@features/run-measurement/model/measurementStore';
import { AlgorithmCardsGrid } from '@widgets/algorithm-cards-grid/ui/AlgorithmCardsGrid';
import { ConsensusDashboard } from '@widgets/consensus-dashboard/ui/ConsensusDashboard';
import { MeasurementProgress } from '@widgets/measurement-progress/ui/MeasurementProgress';
import { MetricsGlossary } from '@widgets/metrics-glossary';
import { StressFormula } from '@widgets/stress-formula';

const PLACEHOLDER_RESULTS: AlgorithmResult[] = ALGORITHM_DEFAULTS.map((m) => ({
  meta: m,
  available: false,
  error: '녹화 후 자동으로 측정됩니다',
  bvpSparkline: [],
  computeMs: 0,
}));

function fmtMs(ms: number) {
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(1)} 초`;
}

export function MeasurePage() {
  const { data } = useMeasurement();
  const reset = useMeasurementStore((s) => s.reset);
  const algorithms = data?.algorithms ?? PLACEHOLDER_RESULTS;
  const inFlight = data && data.status !== 'done' && data.status !== 'failed';
  const isDone = data?.status === 'done';

  return (
    <main className="max-w-6xl mx-auto p-6 flex flex-col gap-6">
      <header className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-bold">rPPG Stress Demo</h1>
          <p className="text-sm text-neutral-500 mt-1">
            웹캠으로 얼굴을 N초 녹화하면 8개 알고리즘이 심박 / HRV / 스트레스 지수를 추출합니다.
          </p>
        </div>
      </header>

      {!data && <RecordPanel />}

      {data?.status === 'failed' && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 flex items-center justify-between">
          <span>측정 실패: {data.error ?? '알 수 없는 오류'}</span>
          <button
            onClick={reset}
            className="ml-3 px-3 py-1.5 rounded-full bg-rose-600 text-white text-xs font-semibold hover:bg-rose-700"
          >
            다시 분석하기
          </button>
        </div>
      )}

      {inFlight && (
        <MeasurementProgress
          progress={data!.progress}
          stage={data!.stage ?? ''}
          status={data!.status}
        />
      )}

      {isDone && data?.timing && (
        <section className="rounded-2xl border bg-white p-4 shadow-sm flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-xs text-neutral-500 uppercase tracking-wider">분석 시간</span>
            <span className="font-semibold tabular-nums">{fmtMs(data.timing.totalMs)}</span>
          </div>
          <span className="text-xs text-neutral-500 tabular-nums">
            영상 길이 {data.timing.videoDurationS.toFixed(1)} 초
          </span>
          <span className="text-xs text-neutral-400 tabular-nums">
            영상 디코드 {fmtMs(data.timing.decodeMs)} · 얼굴 추적 {fmtMs(data.timing.faceRoiMs)} · 품질 평가{' '}
            {fmtMs(data.timing.qualityMs)}
          </span>
          <button
            onClick={reset}
            className="ml-auto px-4 py-2 rounded-full bg-sky-500 text-white text-sm font-semibold hover:bg-sky-600 shadow-sm"
          >
            다시 분석하기
          </button>
        </section>
      )}

      {data?.consensus && (
        <ConsensusDashboard data={data.consensus} totalAlgorithms={ALGORITHM_DEFAULTS.length} />
      )}

      <MetricsGlossary />

      <AlgorithmCardsGrid results={algorithms} />

      <StressFormula />

      {data?.warnings && data.warnings.length > 0 && (
        <ul className="text-sm text-amber-700 list-disc list-inside bg-amber-50 border border-amber-200 rounded-2xl p-4">
          {data.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}

      {isDone && (
        <div className="flex justify-center pt-2">
          <button
            onClick={reset}
            className="px-6 py-3 rounded-full bg-sky-500 text-white text-sm font-semibold hover:bg-sky-600 shadow-sm"
          >
            다시 분석하기
          </button>
        </div>
      )}

      <footer className="text-xs text-neutral-500 border-t pt-4">
        ⚠ Not a medical device. Educational / research use only.
      </footer>
    </main>
  );
}
