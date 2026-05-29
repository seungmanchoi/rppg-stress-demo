/**
 * "스트레스 지수가 어떻게 계산되는가" 설명 패널.
 * 백엔드 산출 공식과 1:1로 동기화되어 있으니, 공식이 바뀌면 여기도 함께 수정.
 */
export function StressFormula() {
  return (
    <details className="rounded-2xl bg-white border p-5 shadow-sm group">
      <summary className="cursor-pointer flex items-center justify-between font-semibold text-base">
        <span>스트레스 지수는 이렇게 계산됩니다</span>
        <span className="text-neutral-400 group-open:rotate-180 transition-transform">⌄</span>
      </summary>

      <div className="mt-4 grid gap-5 md:grid-cols-2 text-sm">
        <Section title="① BVP → IBI" desc="각 알고리즘이 추정한 BVP 파형을 0.7~3.5 Hz로 대역통과 → scipy.find_peaks로 systolic peak를 검출 → 인접 peak 간 간격(IBI, ms)을 산출. median ± 3·MAD로 이상치 제거." />
        <Section
          title="② HRV 메트릭"
          codes={[
            ['SDNN', 'NN 간격의 표준편차 — 전반적 자율신경 활성도'],
            ['RMSSD', '√mean((diff IBI)²) — 부교감 활성 (이완 시 ↑)'],
            ['pNN50', '인접 IBI 차이가 50ms 초과하는 비율'],
            ['LF / HF', 'Lomb-Scargle PSD로 0.04~0.15 / 0.15~0.4 Hz 대역 적분'],
            ['LF/HF ratio', '교감 ↔ 부교감 균형 (스트레스 시 ↑)'],
            ['SD1, SD2', 'Poincaré plot — IBI 시계열의 비선형 변동성'],
          ]}
        />
        <Section
          title="③ Baevsky Stress Index"
          code={`Mo  = mode(IBI, 50ms bin)
AMo = Mo bin 비율(%)
MxDMn = max(IBI) − min(IBI)   (sec)
SI = AMo / (2 · Mo · MxDMn)`}
          desc="러시아 우주의학에서 유래한 자율신경 긴장도 지표. 50–150 정상 / 150–500 약한 스트레스 / 500–900 중등도 / >900 고스트레스."
        />
        <Section
          title="④ Composite Stress Score (0~100)"
          code={`s_baevsky = clip(log10(SI/50) / log10(1500/50), 0, 1)
s_lfhf    = clip((LF/HF - 0.5) / 4.0,     0, 1)
s_rmssd   = clip(1 − RMSSD/60,            0, 1)

Score = 100 · (0.4·s_baevsky + 0.4·s_lfhf + 0.2·s_rmssd)`}
          desc="세 지표를 0~1로 정규화한 뒤 가중 합. Baevsky와 LF/HF는 ↑일수록 스트레스 ↑, RMSSD는 ↓일수록 스트레스 ↑. 등급: 0–30 low / 30–60 mid / 60–80 high / 80–100 very_high."
        />
        <Section
          title="⑤ Reliability Score (각 카드 신뢰도)"
          code={`snr      = clip((SNR_dB + 5) / 15,      0, 1)
tracking = clip(face_detected_ratio,     0, 1)
motion   = clip(1 − mean_optical_flow/5, 0, 1)
agree    = clip(1 − |HR − median_HR|/10, 0, 1)

Reliability = 100 · (0.30·snr + 0.25·tracking
                   + 0.20·motion + 0.25·agree)`}
          desc="신호 자체의 SNR + 얼굴 검출 안정성 + 움직임 패널티 + 다른 알고리즘과의 HR 일치도를 결합. 등급: ≥75 high / 45–75 medium / <45 low."
        />
        <Section
          title="⑥ Consensus (상단 게이지)"
          code={`w_i  = max(reliability_i − 30, 0)
consensus_HR    = weighted_median(HR_i,    w_i)
consensus_Stress = weighted_median(Score_i, w_i)
consensus_reliability = weighted_mean(rel_i, w_i)`}
          desc="reliability가 30 초과인 카드만 가중치 부여, 가중 중앙값으로 합의. 일부 알고리즘이 이상치를 내도 다수가 일관되면 안정적으로 수렴."
        />
      </div>
    </details>
  );
}

function Section({
  title,
  desc,
  code,
  codes,
}: {
  title: string;
  desc?: string;
  code?: string;
  codes?: [string, string][];
}) {
  return (
    <div className="space-y-2">
      <h4 className="font-semibold text-neutral-800">{title}</h4>
      {desc && <p className="text-neutral-600 leading-relaxed">{desc}</p>}
      {code && (
        <pre className="bg-neutral-50 border border-neutral-200 rounded-lg p-3 text-[11px] leading-snug overflow-x-auto whitespace-pre">
          {code}
        </pre>
      )}
      {codes && (
        <dl className="text-xs space-y-1">
          {codes.map(([k, v]) => (
            <div key={k} className="grid grid-cols-[80px_1fr] gap-2">
              <dt className="font-mono text-neutral-800">{k}</dt>
              <dd className="text-neutral-600">{v}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}
