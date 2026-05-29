import type { AlgorithmResult } from '@entities/measurement';

import { BvpSparkline } from './BvpSparkline';
import { MetricRow } from './MetricRow';
import { ReliabilityBadge } from './ReliabilityBadge';

export function AlgorithmResultCard({ result }: { result: AlgorithmResult }) {
  const { meta, available, hrv, stress, reliability, bvpSparkline, error, extras } = result;
  const trained =
    meta.type === 'supervised' && meta.pretrainedOn
      ? `trained on ${meta.pretrainedOn}`
      : 'signal processing';

  return (
    <div
      data-testid="algorithm-card"
      className={`rounded-2xl border bg-white p-5 shadow-sm flex flex-col gap-3 ${
        available ? '' : 'opacity-60'
      }`}
    >
      <header className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="font-semibold text-base">{meta.displayName}</h3>
          <p className="text-xs text-neutral-500 mt-0.5 leading-snug">{meta.shortDescription}</p>
          <p className="text-[10px] text-neutral-400 mt-1 uppercase tracking-wider">{trained}</p>
        </div>
        {available && reliability ? (
          <ReliabilityBadge grade={reliability.grade} score={reliability.score} />
        ) : (
          <span className="text-xs px-2 py-1 rounded-full bg-neutral-100 text-neutral-600 border border-neutral-200">
            pending
          </span>
        )}
      </header>

      {available ? (
        <>
          <BvpSparkline data={bvpSparkline} />

          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
            <MetricRow label="HR" value={`${hrv ? Math.round(hrv.hrBpm) : '-'} BPM`} />
            <MetricRow label="RMSSD" value={`${hrv ? Math.round(hrv.rmssdMs) : '-'} ms`} />
            <MetricRow label="LF/HF" value={hrv ? hrv.lfHfRatio.toFixed(2) : '-'} />
            <MetricRow label="Baev SI" value={stress ? Math.round(stress.baevskySi).toString() : '-'} />
            <MetricRow
              label="Stress"
              highlight
              value={
                stress ? `${Math.round(stress.compositeScore)} (${stress.compositeLevel})` : '-'
              }
            />
            {extras && typeof extras.respirationRpm === 'number' ? (
              <MetricRow label="호흡" value={`${Math.round(extras.respirationRpm as number)} /min`} />
            ) : null}
          </div>
        </>
      ) : (
        <p className="text-xs text-neutral-500 leading-relaxed">
          {error ?? '추론 어댑터 준비 중'}
        </p>
      )}
    </div>
  );
}
