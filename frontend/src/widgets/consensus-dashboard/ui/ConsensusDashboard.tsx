import type { ConsensusResult } from '@entities/measurement';
import { ReliabilityBadge } from '@features/algorithm-result-card/ui/ReliabilityBadge';

import { StressGauge } from './StressGauge';

export function ConsensusDashboard({
  data,
  totalAlgorithms,
}: {
  data: ConsensusResult;
  totalAlgorithms: number;
}) {
  return (
    <section className="rounded-3xl bg-white border p-6 flex flex-wrap items-center gap-6 shadow-sm">
      <StressGauge score={data.stressScore} level={data.stressLevel} />
      <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm min-w-[220px]">
        <Metric label="HR" value={`${Math.round(data.hrBpm)} BPM`} />
        <Metric label="RMSSD" value={`${Math.round(data.rmssdMs)} ms`} />
        <Metric label="LF/HF" value={data.lfHfRatio.toFixed(2)} />
        <Metric label="Baevsky SI" value={Math.round(data.baevskySi).toString()} />
      </div>
      <div className="ml-auto flex flex-col items-end gap-2">
        <ReliabilityBadge grade={data.reliability.grade} score={data.reliability.score} />
        <span className="text-xs text-neutral-500">
          {data.contributingAlgorithms} / {totalAlgorithms} algorithms contributed
        </span>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-neutral-500 uppercase tracking-wider">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}
