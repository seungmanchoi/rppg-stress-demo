import { ALGORITHM_DEFAULTS } from '@entities/algorithm/model/registry';
import type { AlgorithmResult } from '@entities/measurement';
import { useMeasurement } from '@features/run-measurement/model/useMeasurement';
import { useMeasurementStore } from '@features/run-measurement/model/measurementStore';
import { UploadDropzone } from '@features/upload-video/ui/UploadDropzone';
import { AlgorithmCardsGrid } from '@widgets/algorithm-cards-grid/ui/AlgorithmCardsGrid';
import { ConsensusDashboard } from '@widgets/consensus-dashboard/ui/ConsensusDashboard';
import { MeasurementProgress } from '@widgets/measurement-progress/ui/MeasurementProgress';

const PLACEHOLDER_RESULTS: AlgorithmResult[] = ALGORITHM_DEFAULTS.map((m) => ({
  meta: m,
  available: false,
  error: '영상 업로드 후 측정됩니다',
  bvpSparkline: [],
  computeMs: 0,
}));

export function MeasurePage() {
  const { data } = useMeasurement();
  const reset = useMeasurementStore((s) => s.reset);
  const algorithms = data?.algorithms ?? PLACEHOLDER_RESULTS;
  const inFlight = data && data.status !== 'done' && data.status !== 'failed';

  return (
    <main className="max-w-6xl mx-auto p-6 flex flex-col gap-6">
      <header className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-bold">rPPG Stress Demo</h1>
          <p className="text-sm text-neutral-500 mt-1">
            얼굴 영상을 업로드하면 8개 알고리즘이 각각 심박 / HRV / 스트레스 지수를 추출합니다.
          </p>
        </div>
        {data && (
          <button
            onClick={reset}
            className="text-xs text-neutral-500 hover:text-neutral-800 underline"
          >
            새 측정
          </button>
        )}
      </header>

      {!data && <UploadDropzone />}

      {data?.status === 'failed' && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          측정 실패: {data.error ?? '알 수 없는 오류'}
          <button onClick={reset} className="ml-3 underline">
            다시 시도
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

      {data?.consensus && (
        <ConsensusDashboard data={data.consensus} totalAlgorithms={ALGORITHM_DEFAULTS.length} />
      )}

      <AlgorithmCardsGrid results={algorithms} />

      {data?.warnings && data.warnings.length > 0 && (
        <ul className="text-sm text-amber-700 list-disc list-inside bg-amber-50 border border-amber-200 rounded-2xl p-4">
          {data.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}

      <footer className="text-xs text-neutral-500 border-t pt-4">
        ⚠ Not a medical device. Educational / research use only.
      </footer>
    </main>
  );
}
