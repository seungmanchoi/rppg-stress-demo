import { useState } from 'react';

import type { ConsensusResult } from '@entities/measurement';
import { ReliabilityBadge } from '@features/algorithm-result-card/ui/ReliabilityBadge';
import { RELIABILITY_BANDS, stressBand } from '@shared/lib/labels';

import { StressBandsGuide } from './StressBandsGuide';
import { StressGauge } from './StressGauge';

type MetricKey =
  | 'hrBpm' | 'rmssdMs' | 'sdnnMs' | 'pnn50Pct' | 'lfHfRatio' | 'hfNu' | 'baevskySi'
  | 'sd2Sd1' | 'sampleEntropy' | 'dfaAlpha1' | 'higuchiFd' | 'snsIndex' | 'pnsIndex'
  | 'coherenceScore' | 'respirationRpm';

const METRIC_META: Record<MetricKey, { label: string; unit: string; digits: number; hint?: string }> = {
  hrBpm: { label: '심박수', unit: 'BPM', digits: 0, hint: '평균 심박' },
  rmssdMs: { label: 'RMSSD', unit: 'ms', digits: 0, hint: '부교감 활성' },
  sdnnMs: { label: 'SDNN', unit: 'ms', digits: 0, hint: '전체 변이도' },
  pnn50Pct: { label: 'pNN50', unit: '%', digits: 1, hint: '단기 부교감' },
  lfHfRatio: { label: 'LF/HF', unit: '', digits: 2, hint: '교감 / 부교감 균형' },
  hfNu: { label: 'HF n.u.', unit: '', digits: 0, hint: '부교감 스펙트럼' },
  baevskySi: { label: 'Baevsky SI', unit: '', digits: 0, hint: '자율신경 긴장도' },
  sd2Sd1: { label: 'SD2/SD1', unit: '', digits: 2, hint: 'Poincaré 균형' },
  sampleEntropy: { label: 'SampEn', unit: '', digits: 2, hint: '신호 복잡도' },
  dfaAlpha1: { label: 'DFA α1', unit: '', digits: 2, hint: '단기 스케일링' },
  higuchiFd: { label: 'Higuchi FD', unit: '', digits: 2, hint: '프랙탈 복잡도' },
  snsIndex: { label: 'SNS Index', unit: '', digits: 2, hint: '교감 활성' },
  pnsIndex: { label: 'PNS Index', unit: '', digits: 2, hint: '부교감 활성' },
  coherenceScore: { label: 'Coherence', unit: '/ 3', digits: 2, hint: '심장 coherence' },
  respirationRpm: { label: '호흡수', unit: '/min', digits: 1, hint: '호흡 규칙성' },
};

// Metrics each version's formula actually uses (mirrors backend composite_v*.py).
const METRIC_VIEWS: { key: string; label: string; metrics: MetricKey[]; desc: string }[] = [
  {
    key: 'all',
    label: '전체',
    metrics: ['hrBpm', 'baevskySi', 'lfHfRatio', 'rmssdMs', 'sdnnMs', 'pnn50Pct', 'hfNu', 'sd2Sd1', 'sampleEntropy', 'dfaAlpha1', 'higuchiFd', 'snsIndex', 'pnsIndex', 'coherenceScore', 'respirationRpm'],
    desc: '네 공식이 사용하는 모든 지표의 합의값',
  },
  { key: 'v1', label: 'v1', metrics: ['baevskySi', 'lfHfRatio', 'rmssdMs'], desc: 'v1 클래식 — Baevsky + LF/HF + RMSSD (3 지표)' },
  { key: 'v2', label: 'v2', metrics: ['baevskySi', 'lfHfRatio', 'rmssdMs', 'snsIndex', 'pnsIndex', 'sampleEntropy', 'dfaAlpha1', 'coherenceScore', 'respirationRpm'], desc: 'v2 자율신경 종합 (9 지표)' },
  { key: 'v3', label: 'v3', metrics: ['baevskySi', 'lfHfRatio', 'rmssdMs', 'sdnnMs', 'pnn50Pct', 'sd2Sd1', 'sampleEntropy', 'dfaAlpha1', 'higuchiFd', 'snsIndex', 'pnsIndex', 'coherenceScore'], desc: 'v3 전체 HRV 패널 (12 지표)' },
  { key: 'v4', label: 'v4', metrics: ['rmssdMs', 'baevskySi', 'hfNu', 'sd2Sd1', 'coherenceScore', 'pnn50Pct', 'sampleEntropy', 'lfHfRatio'], desc: 'v4 카메라 적응형 robust (8 지표)' },
];

function formatMetric(value: number, m: { unit: string; digits: number }): string {
  const num = Number.isFinite(value) ? value.toFixed(m.digits) : '-';
  return m.unit ? `${num} ${m.unit}` : num;
}

export function ConsensusDashboard({
  data,
  totalAlgorithms,
}: {
  data: ConsensusResult;
  totalAlgorithms: number;
}) {
  const bandV1 = stressBand(data.stressLevel);
  const bandV2 = stressBand(data.stressLevelV2);
  const bandV3 = stressBand(data.stressLevelV3);
  const bandV4 = stressBand(data.stressLevelV4);
  const relInfo = RELIABILITY_BANDS[data.reliability.grade];

  const [view, setView] = useState('all');
  const activeView = METRIC_VIEWS.find((v) => v.key === view) ?? METRIC_VIEWS[0];

  return (
    <section className="flex flex-col md:flex-row gap-4">
      <div className="rounded-3xl bg-white border p-6 flex flex-col gap-4 shadow-sm flex-1">
        <header>
          <h2 className="font-semibold text-base">통합 측정 결과</h2>
          <p className="text-xs text-neutral-500 mt-0.5">
            {data.contributingAlgorithms} / {totalAlgorithms}개 알고리즘의 reliability-weighted
            median 합의 · 네 가지 스트레스 공식 동시 산출
          </p>
        </header>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
          <ScoreCard
            variant="v3"
            title="스트레스 v3"
            subtitle="v2 + SDNN + pNN50 + SD2/SD1 + Higuchi"
            tag="전체 HRV 패널 · 12 지표"
            score={data.stressScoreV3}
            level={data.stressLevelV3}
            band={bandV3}
          />
          <ScoreCard
            variant="v4"
            title="스트레스 v4"
            subtitle="단기 신뢰 지표 중심 + 측정 신뢰도 가중·중립 보정"
            tag="카메라 적응형 robust · 8 지표"
            score={data.stressScoreV4}
            level={data.stressLevelV4}
            band={bandV4}
          />
        </div>

        <div className="pt-3 border-t">
          <div className="flex items-center justify-between gap-2 mb-2.5">
            <div className="inline-flex rounded-lg bg-neutral-100 p-0.5">
              {METRIC_VIEWS.map((v) => (
                <button
                  key={v.key}
                  type="button"
                  onClick={() => setView(v.key)}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                    v.key === view
                      ? 'bg-white text-neutral-900 shadow-sm'
                      : 'text-neutral-500 hover:text-neutral-800'
                  }`}
                >
                  {v.label}
                </button>
              ))}
            </div>
            <span className="text-[11px] text-neutral-400 hidden sm:block">
              {activeView.metrics.length}개 지표
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-2 text-sm">
            {activeView.metrics.map((key) => {
              const m = METRIC_META[key];
              return <Metric key={key} label={m.label} value={formatMetric(data[key], m)} hint={m.hint} />;
            })}
          </div>

          <p className="text-[11px] text-neutral-400 mt-2">{activeView.desc}</p>
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
  variant: 'v1' | 'v2' | 'v3' | 'v4';
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
