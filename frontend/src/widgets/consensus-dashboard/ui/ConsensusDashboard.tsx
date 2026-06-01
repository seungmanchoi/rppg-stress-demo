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
  const bandV1 = stressBand(data.stressLevel);
  const bandV2 = stressBand(data.stressLevelV2);
  const relInfo = RELIABILITY_BANDS[data.reliability.grade];

  return (
    <section className="flex flex-col md:flex-row gap-4">
      <div className="rounded-3xl bg-white border p-6 flex flex-col gap-4 shadow-sm flex-1">
        <header>
          <h2 className="font-semibold text-base">통합 측정 결과</h2>
          <p className="text-xs text-neutral-500 mt-0.5">
            {data.contributingAlgorithms} / {totalAlgorithms}개 알고리즘의 reliability-weighted
            median 합의 · 두 가지 스트레스 공식 동시 산출
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ScoreCard
            variant="v1"
            title="스트레스 v1"
            subtitle="Baevsky + LF/HF + RMSSD"
            tag="클래식 · 3 지표"
            score={data.stressScore}
            level={data.stressLevel}
            band={bandV1}
          />
          <ScoreCard
            variant="v2"
            title="스트레스 v2"
            subtitle="v1 + Kubios + HeartMath + SampEn + DFA α1 + 호흡"
            tag="자율신경 종합 · 9 지표"
            score={data.stressScoreV2}
            level={data.stressLevelV2}
            band={bandV2}
          />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-2 text-sm pt-3 border-t">
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
          <ReliabilityBadge grade={data.reliability.grade} score={data.reliability.score} />
        </div>
      </div>

      <StressBandsGuide currentLevel={data.stressLevel} />
    </section>
  );
}

function ScoreCard({
  variant,
  title,
  subtitle,
  tag,
  score,
  level,
  band,
}: {
  variant: 'v1' | 'v2';
  title: string;
  subtitle: string;
  tag: string;
  score: number;
  level: import('@entities/measurement').StressLevel;
  band: ReturnType<typeof stressBand>;
}) {
  return (
    <div
      className="rounded-2xl border p-4 flex flex-col gap-3"
      style={{
        backgroundColor: `${band.color}0d`,
        borderColor: `${band.color}55`,
      }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-base" style={{ color: band.color }}>
              {title}
            </h3>
            <span
              className="text-[9px] font-mono px-1.5 py-0.5 rounded uppercase tracking-wider"
              style={{
                backgroundColor: `${band.color}22`,
                color: band.color,
              }}
            >
              {variant}
            </span>
          </div>
          <p className="text-[11px] text-neutral-500 mt-0.5 leading-snug">{subtitle}</p>
          <p className="text-[10px] text-neutral-400 mt-0.5">{tag}</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <StressGauge score={score} level={level} />
        <div className="flex-1 min-w-0">
          <div className="text-xs text-neutral-500">현재 상태</div>
          <div className="text-lg font-semibold leading-tight" style={{ color: band.color }}>
            {band.full}
          </div>
          <p className="text-[11px] text-neutral-600 mt-1 leading-relaxed">{band.description}</p>
        </div>
      </div>
    </div>
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
