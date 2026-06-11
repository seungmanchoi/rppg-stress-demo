import { useState } from 'react';

import { ALGORITHM_DETAILS } from '@entities/algorithm/model/registry';
import type { AlgorithmId, AlgorithmResult } from '@entities/measurement';
import { BAEVSKY_BANDS } from '@shared/lib/labels';
import { TIER_STYLES, type MetricTier } from '@shared/lib/metricTiers';

import { BvpSparkline } from './BvpSparkline';
import { MetricRow } from './MetricRow';
import { ReliabilityBadge } from './ReliabilityBadge';
import { StressBreakdown } from './StressBreakdown';

const fmt = (n: number | undefined | null, digits = 1, fallback = '-') =>
  n === undefined || n === null || !Number.isFinite(n) ? fallback : n.toFixed(digits);

export function AlgorithmResultCard({ result }: { result: AlgorithmResult }) {
  const {
    meta,
    available,
    hrv,
    stress,
    reliability,
    respiration,
    hemodynamic,
    signalQuality,
    beatCount,
    bvpSparkline,
    error,
  } = result;
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
          <div className="flex items-baseline justify-between -mt-1">
            <span className="text-[10px] uppercase tracking-wider text-neutral-400">BVP</span>
            <span className="text-[10px] text-neutral-400 tabular-nums">
              {beatCount ? `${beatCount} 박동 · ` : ''}처리 {Math.round(result.computeMs)} ms
            </span>
          </div>
          <BvpSparkline data={bvpSparkline} />

          {/* 핵심 HRV (clinical) */}
          <TierBox tier="clinical" label="핵심 HRV (임상 표준)">
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
              <MetricRow label="심박수" value={`${hrv ? Math.round(hrv.hrBpm) : '-'} BPM`} />
              <MetricRow label="IBI mean" value={`${fmt(hrv?.ibiMeanMs, 0)} ms`} />
              <MetricRow label="SDNN" value={`${fmt(hrv?.sdnnMs, 0)} ms`} />
              <MetricRow label="RMSSD" value={`${fmt(hrv?.rmssdMs, 0)} ms`} />
              <MetricRow label="SDSD" value={`${fmt(hrv?.sdsdMs, 0)} ms`} />
              <MetricRow label="pNN50" value={`${fmt(hrv?.pnn50Pct, 1)} %`} />
              <MetricRow label="pNN20" value={`${fmt(hrv?.pnn20Pct, 1)} %`} />
              <MetricRow label="CVnn" value={`${fmt(hrv?.cvnnPct, 2)} %`} />
              <MetricRow label="HRV TI" value={fmt(hrv?.hrvTriangularIndex, 1)} />
              <MetricRow label="LF/HF" value={fmt(hrv?.lfHfRatio, 2)} />
              <MetricRow
                label="LFnu / HFnu"
                value={`${fmt(hrv?.lfNu, 0)} / ${fmt(hrv?.hfNu, 0)}`}
              />
              <MetricRow
                label="Baev SI"
                value={
                  stress
                    ? `${Math.round(stress.baevskySi)} (${BAEVSKY_BANDS[stress.baevskyLevel].label})`
                    : '-'
                }
              />
              <MetricRow label="SD1 / SD2" value={`${fmt(hrv?.sd1, 0)} / ${fmt(hrv?.sd2, 0)}`} />
            </div>
          </TierBox>

          {/* 스트레스 v1 — 기존 클래식 (Baev + LF/HF + RMSSD) */}
          {stress?.compositeV1 && (
            <StressBreakdown
              title="스트레스 v1 — 클래식"
              subtitle="Baevsky + LF/HF + RMSSD (3 지표)"
              data={stress.compositeV1}
            />
          )}

          {/* 스트레스 v2 — 자율신경 균형 종합 (9 지표) */}
          {stress?.compositeV2 && (
            <StressBreakdown
              title="스트레스 v2 — 자율신경 종합"
              subtitle="v1의 3 지표 + Kubios + HeartMath + SampEn + DFA α1 + 호흡 (총 9 지표)"
              data={stress.compositeV2}
            />
          )}

          {/* 스트레스 v3 — 전체 HRV 패널 종합 (12 지표) */}
          {stress?.compositeV3 && (
            <StressBreakdown
              title="스트레스 v3 — 전체 HRV 패널"
              subtitle="v2 + SDNN + pNN50 + SD2/SD1 + Higuchi (총 12 지표) — 가장 폭넓은 종합"
              data={stress.compositeV3}
            />
          )}

          {/* 스트레스 v4 — 카메라 단기 측정 적응형 robust */}
          {stress?.compositeV4 && (
            <StressBreakdown
              title="스트레스 v4 — 카메라 적응형"
              subtitle="단기 신뢰 지표(RMSSD·HF·Baevsky·SD2/SD1·coherence) 중심 + 측정 신뢰도로 가중·중립 보정"
              data={stress.compositeV4}
            />
          )}

          {/* 상용 표준: Kubios + HeartMath */}
          {stress && (
            <TierBox tier="commercial" label="상용 표준 — Kubios · HeartMath">
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                <MetricRow label="PNS Index" value={fmt(stress.pnsIndex, 2)} />
                <MetricRow label="SNS Index" value={fmt(stress.snsIndex, 2)} />
                <MetricRow label="Coherence" value={`${fmt(stress.coherenceScore, 2)} / 3`} />
                <MetricRow label="공명 주파수" value={`${fmt(stress.coherencePeakHz, 3)} Hz`} />
                <MetricRow label="AMo" value={`${fmt(stress.baevskyAmoPct, 1)} %`} />
                <MetricRow label="MxDMn" value={`${fmt(stress.baevskyMxdmnS, 2)} s`} />
                <MetricRow label="Mo (mode IBI)" value={`${fmt(stress.baevskyMoS, 2)} s`} />
              </div>
            </TierBox>
          )}

          {/* 호흡 (commercial) */}
          {respiration && respiration.rateRpm > 0 && (
            <TierBox tier="commercial" label="호흡 — BVP envelope (Karlen 2013)">
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                <MetricRow label="호흡수" value={`${fmt(respiration.rateRpm, 1)} /min`} />
                <MetricRow label="신뢰도" value={fmt(respiration.confidence, 2)} />
              </div>
            </TierBox>
          )}

          {/* 학계 검증: 비선형 + 주파수 + 신호 품질 */}
          <TierBox tier="research" label="비선형 HRV · 학계 검증">
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
              <MetricRow label="SD2/SD1" value={fmt(hrv?.sdRatio, 2)} />
              <MetricRow label="Ellipse Area" value={`${fmt(hrv?.ellipseArea, 0)} ms²`} />
              <MetricRow label="Sample Entropy" value={fmt(hrv?.sampleEntropy, 2)} />
              <MetricRow label="Approx. Entropy" value={fmt(hrv?.approximateEntropy, 2)} />
              <MetricRow label="Shannon Entropy" value={`${fmt(hrv?.shannonEntropy, 2)} bits`} />
              <MetricRow label="DFA α1" value={fmt(hrv?.dfaAlpha1, 2)} />
              <MetricRow label="Higuchi FD" value={fmt(hrv?.higuchiFd, 2)} />
              <MetricRow label="LF / HF Power" value={`${fmt(hrv?.lfPower, 1)} / ${fmt(hrv?.hfPower, 1)}`} />
              <MetricRow label="Total Power" value={`${fmt(hrv?.totalPower, 1)} ms²`} />
              {signalQuality && (
                <>
                  <MetricRow label="PQI" value={`${fmt(signalQuality.pqi, 0)} / 100`} />
                  <MetricRow label="Spec. Entropy" value={fmt(signalQuality.spectralEntropy, 3)} />
                </>
              )}
            </div>
          </TierBox>

          {/* 실험적: VLF + Pulse morphology */}
          <TierBox tier="experimental" label="실험적 — VLF · 맥파 형태">
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
              <MetricRow label="VLF Power" value={`${fmt(hrv?.vlfPower, 1)} ms²`} />
              {hemodynamic && (
                <MetricRow
                  label="Pulse Rise Time"
                  value={`${fmt(hemodynamic.pulseRiseTimeMs, 0)} ms`}
                />
              )}
            </div>
          </TierBox>

          {/* RGB 추정: SpO2 */}
          {hemodynamic && hemodynamic.spo2Pct > 0 && (
            <TierBox tier="rgbEstimated" label="RGB 추정 — 의료기기 대비 큰 오차 가능">
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                <MetricRow label="SpO2" value={`${fmt(hemodynamic.spo2Pct, 1)} %`} />
                <MetricRow label="SpO2 신뢰도" value={fmt(hemodynamic.spo2Confidence, 2)} />
              </div>
            </TierBox>
          )}

          {reliability?.components && (
            <div className="rounded-lg border border-neutral-200 bg-neutral-50/60 px-3 py-2 text-[11px] leading-snug">
              <div className="flex items-baseline justify-between mb-1.5">
                <span className="uppercase tracking-wider text-neutral-500">신뢰도 세부</span>
                <span className="text-neutral-700 tabular-nums">
                  합의 가중치 <b className="font-semibold">{Math.max(0, Math.round(reliability.score - 30))}</b> / 70
                </span>
              </div>
              <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-neutral-700 tabular-nums">
                <ReliabilityRow
                  label="신호품질 (SNR)"
                  value={`${reliability.components.snrDb.toFixed(1)} dB`}
                  weight="30%"
                />
                <ReliabilityRow
                  label="얼굴 추적"
                  value={`${reliability.components.faceTrackingPct.toFixed(0)} %`}
                  weight="25%"
                />
                <ReliabilityRow
                  label="HR 편차"
                  value={`${reliability.components.deviationFromConsensus >= 0 ? '+' : ''}${reliability.components.deviationFromConsensus.toFixed(1)} BPM`}
                  weight="25%"
                />
                <ReliabilityRow
                  label="움직임"
                  value={`${reliability.components.motionPenalty.toFixed(1)} px`}
                  weight="20%"
                />
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="space-y-1">
          <p className="text-xs text-neutral-500 leading-relaxed">{error ?? '추론 어댑터 준비 중'}</p>
          {result.computeMs > 0 && (
            <p className="text-[10px] text-neutral-400 tabular-nums">
              처리 {Math.round(result.computeMs)} ms
            </p>
          )}
        </div>
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

function TierBox({
  tier,
  label,
  children,
}: {
  tier: MetricTier;
  label: string;
  children: React.ReactNode;
}) {
  const s = TIER_STYLES[tier];
  return (
    <div className={`rounded-lg border ${s.boxClass} px-3 py-2`}>
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="text-[10px] uppercase tracking-wider text-neutral-600 font-semibold">
          {label}
        </span>
        <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${s.chipClass}`}>
          {s.badge}
        </span>
      </div>
      {children}
    </div>
  );
}

function ReliabilityRow({ label, value, weight }: { label: string; value: string; weight: string }) {
  return (
    <div className="flex items-baseline justify-between gap-2 min-w-0">
      <span className="text-neutral-500 truncate">
        {label} <span className="text-neutral-400">· {weight}</span>
      </span>
      <span className="text-neutral-800 font-medium shrink-0">{value}</span>
    </div>
  );
}
