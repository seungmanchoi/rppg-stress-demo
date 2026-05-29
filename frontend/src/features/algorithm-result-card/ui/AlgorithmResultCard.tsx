import { useState } from 'react';

import { ALGORITHM_DETAILS } from '@entities/algorithm/model/registry';
import type { AlgorithmId, AlgorithmResult } from '@entities/measurement';
import { BAEVSKY_BANDS, stressBand } from '@shared/lib/labels';

import { BvpSparkline } from './BvpSparkline';
import { MetricRow } from './MetricRow';
import { ReliabilityBadge } from './ReliabilityBadge';

export function AlgorithmResultCard({ result }: { result: AlgorithmResult }) {
  const { meta, available, hrv, stress, reliability, bvpSparkline, error, extras } = result;
  const details = ALGORITHM_DETAILS[meta.id as AlgorithmId];
  const [expanded, setExpanded] = useState(false);

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
            <MetricRow label="심박수" value={`${hrv ? Math.round(hrv.hrBpm) : '-'} BPM`} />
            <MetricRow label="RMSSD" value={`${hrv ? Math.round(hrv.rmssdMs) : '-'} ms`} />
            <MetricRow label="LF/HF" value={hrv ? hrv.lfHfRatio.toFixed(2) : '-'} />
            <MetricRow
              label="Baev SI"
              value={
                stress
                  ? `${Math.round(stress.baevskySi)} (${BAEVSKY_BANDS[stress.baevskyLevel].label})`
                  : '-'
              }
            />
            {extras && typeof extras.respirationRpm === 'number' ? (
              <MetricRow label="호흡" value={`${Math.round(extras.respirationRpm as number)} /min`} />
            ) : null}
          </div>
          {stress && (
            <div
              className="rounded-lg px-3 py-2 text-sm flex items-baseline justify-between"
              style={{
                backgroundColor: `${stressBand(stress.compositeLevel).color}1a`,
                color: stressBand(stress.compositeLevel).color,
              }}
            >
              <span className="text-[11px] uppercase tracking-wider opacity-80">스트레스</span>
              <span className="font-semibold">
                {Math.round(stress.compositeScore)} / 100 · {stressBand(stress.compositeLevel).label}
              </span>
            </div>
          )}
        </>
      ) : (
        <p className="text-xs text-neutral-500 leading-relaxed">{error ?? '추론 어댑터 준비 중'}</p>
      )}

      {details && (
        <details
          className="mt-1 border-t pt-2 group"
          open={expanded}
          onToggle={(e) => setExpanded((e.target as HTMLDetailsElement).open)}
        >
          <summary className="cursor-pointer text-[11px] uppercase tracking-wider text-neutral-500 hover:text-neutral-800 select-none flex items-center justify-between">
            <span>분석 방식</span>
            <span className="text-neutral-400 group-open:rotate-180 transition-transform">⌄</span>
          </summary>
          <div className="mt-2 space-y-2 text-[12px] leading-relaxed text-neutral-700">
            <div>
              <span className="font-semibold text-neutral-800">분석 대상</span>
              <p className="mt-0.5 text-neutral-600">{details.analyzes}</p>
            </div>
            <div>
              <span className="font-semibold text-neutral-800">방법</span>
              <p className="mt-0.5 text-neutral-600">{details.methodology}</p>
            </div>
            {details.citation && (
              <p className="text-[10px] text-neutral-400 italic">— {details.citation}</p>
            )}
          </div>
        </details>
      )}
    </div>
  );
}
