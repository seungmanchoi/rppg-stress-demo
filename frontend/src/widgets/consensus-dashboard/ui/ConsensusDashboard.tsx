import type { ConsensusResult } from '@entities/measurement';
import { ReliabilityBadge } from '@features/algorithm-result-card/ui/ReliabilityBadge';
import { RELIABILITY_BANDS, stressBand } from '@shared/lib/labels';

import { StressBandsGuide } from './StressBandsGuide';
import { StressGauge } from './StressGauge';

export function ConsensusDashboard({
  data,
  totalAlgorithms,
}: {
  data: ConsensusResult;
  totalAlgorithms: number;
}) {
  const band = stressBand(data.stressLevel);
  const relInfo = RELIABILITY_BANDS[data.reliability.grade];

  return (
    <section className="flex flex-col md:flex-row gap-4">
      <div className="rounded-3xl bg-white border p-6 flex flex-col gap-4 shadow-sm flex-1">
        <header>
          <h2 className="font-semibold text-base">통합 측정 결과</h2>
          <p className="text-xs text-neutral-500 mt-0.5">
            {data.contributingAlgorithms} / {totalAlgorithms}개 알고리즘의 reliability-weighted
            median 합의
          </p>
        </header>

        <div className="flex flex-wrap items-center gap-6">
          <StressGauge score={data.stressScore} level={data.stressLevel} />

          <div className="flex-1 min-w-[220px] flex flex-col gap-3">
            <div className="text-sm">
              <div className="text-xs text-neutral-500">현재 상태</div>
              <div className="text-lg font-semibold" style={{ color: band.color }}>
                {band.full}
              </div>
              <p className="text-xs text-neutral-600 mt-1 leading-relaxed">{band.description}</p>
            </div>

            <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm pt-2 border-t">
              <Metric label="심박수" value={`${Math.round(data.hrBpm)} BPM`} />
              <Metric label="RMSSD" value={`${Math.round(data.rmssdMs)} ms`} hint="부교감 활성" />
              <Metric label="LF/HF" value={data.lfHfRatio.toFixed(2)} hint="교감 / 부교감 균형" />
              <Metric
                label="Baevsky SI"
                value={Math.round(data.baevskySi).toString()}
                hint="자율신경 긴장도"
              />
            </div>

            <div className="flex items-center justify-between pt-2 border-t">
              <div>
                <div className="text-xs text-neutral-500">측정 신뢰도</div>
                <div className="text-sm font-medium">
                  {relInfo.full} · {Math.round(data.reliability.score)} / 100
                </div>
                <p className="text-[11px] text-neutral-500 mt-0.5">{relInfo.description}</p>
              </div>
              <ReliabilityBadge
                grade={data.reliability.grade}
                score={data.reliability.score}
              />
            </div>
          </div>
        </div>
      </div>

      <StressBandsGuide currentLevel={data.stressLevel} />
    </section>
  );
}

function Metric({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div>
      <div className="text-[11px] text-neutral-500 uppercase tracking-wider">{label}</div>
      <div className="text-base font-semibold">{value}</div>
      {hint && <div className="text-[10px] text-neutral-400">{hint}</div>}
    </div>
  );
}
