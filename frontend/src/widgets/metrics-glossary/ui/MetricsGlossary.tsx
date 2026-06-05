import { TIER_ORDER, TIER_STYLES, type MetricTier } from '@shared/lib/metricTiers';

interface MetricEntry {
  name: string;
  unit?: string;
  normal?: string;
  meaning: string;
  tier: MetricTier;
}

interface MetricGroup {
  title: string;
  hint: string;
  items: MetricEntry[];
}

const GROUPS: MetricGroup[] = [
  {
    title: 'HRV — 시간 영역 (Time-domain)',
    hint: '심박 간격(IBI) 시간축 통계. ESC/NASPE 1996 Task Force 표준.',
    items: [
      {
        name: '심박수 (HR)',
        unit: 'BPM',
        normal: '안정 시 60~100',
        meaning: '분당 박동 수. 60 000 ÷ 평균 IBI(ms).',
        tier: 'clinical',
      },
      {
        name: 'IBI mean',
        unit: 'ms',
        normal: '600~1000',
        meaning: '평균 박동 간격 (NN interval).',
        tier: 'clinical',
      },
      {
        name: 'SDNN',
        unit: 'ms',
        normal: '50~100 (24h 기준)',
        meaning: '전체 NN 간격의 표준편차. 전반적 자율신경 활성도.',
        tier: 'clinical',
      },
      {
        name: 'RMSSD',
        unit: 'ms',
        normal: '20~80 (이완 시 100+)',
        meaning: '연속 IBI 차이의 RMS. 부교감 활성(이완) 표준 지표.',
        tier: 'clinical',
      },
      {
        name: 'SDSD',
        unit: 'ms',
        normal: 'RMSSD와 유사',
        meaning: '연속 IBI 차이의 표준편차. 단기 변동성.',
        tier: 'clinical',
      },
      {
        name: 'pNN50',
        unit: '%',
        normal: '3~30',
        meaning: '50 ms 초과 차이를 보인 연속 박동의 비율.',
        tier: 'clinical',
      },
      {
        name: 'pNN20',
        unit: '%',
        normal: '30~70',
        meaning: '20 ms 초과 차이 비율. 단시간 측정에 pNN50보다 민감.',
        tier: 'clinical',
      },
      {
        name: 'CVnn',
        unit: '%',
        normal: '3~10',
        meaning: '변동계수 (SDNN/Mean). 정규화된 HRV.',
        tier: 'clinical',
      },
      {
        name: 'HRV Triangular Index',
        unit: '점수',
        normal: '15+',
        meaning: 'IBI 히스토그램 면적 / 피크. 전반적 HRV의 기하학적 지표.',
        tier: 'clinical',
      },
    ],
  },
  {
    title: 'HRV — 주파수 영역 (Frequency-domain)',
    hint: 'IBI 시계열의 Lomb-Scargle PSD. 자율신경 균형의 주파수 분리.',
    items: [
      {
        name: 'VLF Power',
        unit: 'ms²',
        normal: '5분 이상 측정 권장',
        meaning: '초저주파 (0.003~0.04 Hz). 체온/호르몬 조절. 짧은 영상에서는 불안정.',
        tier: 'experimental',
      },
      {
        name: 'LF Power',
        unit: 'ms²',
        normal: '교감+부교감 혼합',
        meaning: '저주파 (0.04~0.15 Hz). 압수용체 반사 (baroreflex).',
        tier: 'clinical',
      },
      {
        name: 'HF Power',
        unit: 'ms²',
        normal: '부교감 신경 지표',
        meaning: '고주파 (0.15~0.4 Hz). 호흡 동조 — 부교감 활성.',
        tier: 'clinical',
      },
      {
        name: 'Total Power',
        unit: 'ms²',
        normal: 'VLF+LF+HF',
        meaning: '전체 PSD 적분. 종합 자율신경 활성도.',
        tier: 'clinical',
      },
      {
        name: 'LF/HF',
        unit: '비율',
        normal: '0.5~2.0 (≈1.0 균형)',
        meaning: '교감/부교감 균형 추정. 높으면 긴장.',
        tier: 'clinical',
      },
      {
        name: 'LFnu / HFnu',
        unit: '%',
        normal: 'LFnu+HFnu=100',
        meaning: 'LF/(LF+HF) 정규화 단위. 총파워 편차 영향 제거.',
        tier: 'clinical',
      },
    ],
  },
  {
    title: 'HRV — 비선형 (Non-linear)',
    hint: '복잡도 / 자기유사성. 학계에서 다수 검증된 진단 지표.',
    items: [
      {
        name: 'Poincaré SD1',
        unit: 'ms',
        normal: '20~50',
        meaning: '단기 변동 (부교감). RMSSD와 강한 상관.',
        tier: 'clinical',
      },
      {
        name: 'Poincaré SD2',
        unit: 'ms',
        normal: '50~150',
        meaning: '장기 변동. 전체 HRV 반영.',
        tier: 'clinical',
      },
      {
        name: 'SD2/SD1',
        unit: '비율',
        normal: '2~5',
        meaning: '장단기 변동 비. 자율신경 균형 종합.',
        tier: 'research',
      },
      {
        name: 'Ellipse Area',
        unit: 'ms²',
        normal: '500~5000',
        meaning: 'π · SD1 · SD2. Poincaré plot의 타원 면적.',
        tier: 'research',
      },
      {
        name: 'Sample Entropy',
        unit: '0~3',
        normal: '1.0~2.0',
        meaning: 'IBI 신호 복잡도 (Richman 2000). 낮으면 규칙적/병적, 높으면 다양함.',
        tier: 'research',
      },
      {
        name: 'Approximate Entropy',
        unit: '0~3',
        normal: '1.0~2.0',
        meaning: '복잡도 (Pincus 1991). SampEn의 전신 — 짧은 신호에 민감.',
        tier: 'research',
      },
      {
        name: 'Shannon Entropy',
        unit: 'bits',
        normal: '2~4',
        meaning: 'IBI 분포의 정보 엔트로피. 균등 분포일수록 큼.',
        tier: 'research',
      },
      {
        name: 'DFA α1',
        unit: '0.5~1.5',
        normal: '≈1.0 건강',
        meaning: '단기 자기유사 지수 (4~16 박동). 0.5=백색잡음, 1.0=1/f, 1.5=무작위행보.',
        tier: 'research',
      },
      {
        name: 'Higuchi FD',
        unit: '1~2',
        normal: '1.3~1.7',
        meaning: '프랙탈 차원. 1=매끄러움, 2=무작위.',
        tier: 'research',
      },
    ],
  },
  {
    title: '스트레스 지수',
    hint: '자율신경 균형을 종합한 단일 점수들.',
    items: [
      {
        name: 'Baevsky SI',
        unit: '점수',
        normal: '50~150',
        meaning: '러시아 우주의학 자율신경 경직도. AMo / (2·Mo·MxDMn). 150~500 약한 긴장, 500+ 고스트레스.',
        tier: 'clinical',
      },
      {
        name: 'AMo (Mode Amplitude)',
        unit: '%',
        normal: '30~50',
        meaning: 'Baevsky 구성요소 — 최빈 IBI 구간의 비율.',
        tier: 'clinical',
      },
      {
        name: 'MxDMn',
        unit: 's',
        normal: '0.2~0.4',
        meaning: 'Baevsky 구성요소 — IBI 최대-최소 차이.',
        tier: 'clinical',
      },
      {
        name: 'Kubios PNS Index',
        unit: '-2 ~ +2',
        normal: '0 ≈ 표준',
        meaning: 'MeanRR · RMSSD · HFnu의 z-mean. + = 부교감 활성 ↑ (이완).',
        tier: 'commercial',
      },
      {
        name: 'Kubios SNS Index',
        unit: '-2 ~ +2',
        normal: '0 ≈ 표준',
        meaning: 'HR · Baevsky · LFnu의 z-mean. + = 교감 활성 ↑ (긴장).',
        tier: 'commercial',
      },
      {
        name: 'HeartMath Coherence',
        unit: '0~3',
        normal: '1.0+ 양호',
        meaning: '0.04~0.26 Hz 공명대 단일 피크의 일관성. 깊은 호흡으로 ↑.',
        tier: 'commercial',
      },
      {
        name: '스트레스 v1 (클래식, 3 지표)',
        unit: '0~100',
        normal: '구간별 라벨',
        meaning: 'norm_baev·0.40 + norm_lfhf·0.40 + norm_rmssd·0.20. ESC/NASPE 1996 + 러시아 Baevsky 보수적 공식.',
        tier: 'clinical',
      },
      {
        name: '스트레스 v2 (자율신경 종합, 9 지표)',
        unit: '0~100',
        normal: '구간별 라벨',
        meaning:
          'v1의 3 지표(0.45) + Kubios SNS·PNS(0.20) + SampEn·DFA α1 dev(0.15) + Coherence·호흡 dev(0.20). 단일 지표 편향 감소.',
        tier: 'research',
      },
      {
        name: '스트레스 v3 (전체 HRV 패널, 12 지표)',
        unit: '0~100',
        normal: '구간별 라벨',
        meaning:
          'v2의 자율신경 지표에 SDNN·pNN50·SD2/SD1·Higuchi FD를 더해 12개로 종합. 임상(0.58)+학계(0.17)+상용(0.25). 카드에 보이는 지표를 최대한 활용 — 가장 폭넓고 노이즈에 강한 점수.',
        tier: 'research',
      },
    ],
  },
  {
    title: '호흡 (Respiratory)',
    hint: 'BVP envelope 0.1~0.5 Hz 분석 (Karlen 2013).',
    items: [
      {
        name: '호흡수 (RR)',
        unit: '/min',
        normal: '12~20',
        meaning: 'BVP 진폭 변조에서 추출한 분당 호흡 수.',
        tier: 'commercial',
      },
      {
        name: '호흡 신뢰도',
        unit: '0~1',
        normal: '0.5+',
        meaning: '호흡 피크의 noise floor 대비 prominence.',
        tier: 'experimental',
      },
    ],
  },
  {
    title: '맥파 형태 / 신호 품질',
    hint: '비트별 모양 일관성과 주파수 도메인 깨끗함.',
    items: [
      {
        name: 'PQI (Pulse Quality Index)',
        unit: '0~100',
        normal: '70+',
        meaning: '비트 템플릿 상관계수 평균 (Elgendi 2016). 박동 모양 일관성.',
        tier: 'research',
      },
      {
        name: 'BVP Spectral Entropy',
        unit: '0~1',
        normal: '0.3 이하',
        meaning: '0.5~4 Hz 대역 정규화 엔트로피. 낮을수록 깨끗한 단일 피크.',
        tier: 'research',
      },
      {
        name: 'Pulse Rise Time',
        unit: 'ms',
        normal: '100~250',
        meaning: '맥파 발끝(foot)에서 systolic peak까지 시간. 동맥 강성 연관.',
        tier: 'experimental',
      },
    ],
  },
  {
    title: '혈역학 (Hemodynamic, RGB 카메라 추정)',
    hint: 'RGB만으로 추정 — 의료기기 대비 정확도 한계.',
    items: [
      {
        name: 'SpO2 (산소포화도)',
        unit: '%',
        normal: '95~100',
        meaning: 'Red/Blue ratio-of-ratios로 추정 (Tarassenko 2014). IR이 없어 ±3~5% 오차.',
        tier: 'rgbEstimated',
      },
      {
        name: 'SpO2 신뢰도',
        unit: '0~1',
        normal: '0.5+',
        meaning: 'AC/DC 진폭비 기반 신뢰도. 어두운 환경/움직임 시 ↓.',
        tier: 'rgbEstimated',
      },
    ],
  },
  {
    title: '신뢰도 / 합의',
    hint: '각 알고리즘 결과의 가중치 결정 방식.',
    items: [
      {
        name: '신호품질 (SNR)',
        unit: 'dB',
        normal: '−5 ~ +10',
        meaning: 'BVP 신호 대 잡음비. 가중치 30%.',
        tier: 'clinical',
      },
      {
        name: '얼굴 추적',
        unit: '%',
        normal: '95% 이상',
        meaning: '영상 중 얼굴이 검출된 프레임 비율. 가중치 25%.',
        tier: 'clinical',
      },
      {
        name: 'HR 편차',
        unit: 'BPM',
        normal: '±5 이내',
        meaning: '8개 알고리즘 HR 중앙값과의 차이. 가중치 25%. ±25 BPM 초과 시 자동 강등.',
        tier: 'clinical',
      },
      {
        name: '움직임',
        unit: 'px',
        normal: '2 미만',
        meaning: '프레임 간 평균 픽셀 이동량. 가중치 20%.',
        tier: 'clinical',
      },
      {
        name: '합의 가중치',
        unit: '0~70',
        meaning: 'max(신뢰도 − 30, 0). 30 미만이면 합의 제외.',
        tier: 'clinical',
      },
    ],
  },
];

export function MetricsGlossary() {
  return (
    <aside className="rounded-3xl bg-white border p-5 shadow-sm flex flex-col gap-5">
      <header>
        <h2 className="font-semibold text-base">측정 지표 안내</h2>
        <p className="text-xs text-neutral-500 mt-0.5">
          각 카드와 합의 대시보드에 표시되는 모든 수치의 의미·정상 범위·신뢰도 등급입니다.
        </p>
      </header>

      <section className="rounded-2xl border border-neutral-200 bg-neutral-50 p-3">
        <h3 className="text-sm font-semibold text-neutral-800 mb-2">신뢰도 등급 (Tier) 범례</h3>
        <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
          {TIER_ORDER.map((tier) => {
            const s = TIER_STYLES[tier];
            return (
              <li
                key={tier}
                className={`rounded-lg border ${s.boxClass} p-2 flex flex-col gap-1`}
              >
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${s.chipClass} self-start`}>
                  {s.badge}
                </span>
                <span className="text-[12px] font-semibold text-neutral-800">{s.label}</span>
                <span className="text-[10px] text-neutral-600 leading-snug">{s.meaning}</span>
              </li>
            );
          })}
        </ul>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {GROUPS.map((g) => (
          <section
            key={g.title}
            className="rounded-2xl border border-neutral-200 bg-neutral-50/40 p-3"
          >
            <h3 className="text-sm font-semibold text-neutral-800">{g.title}</h3>
            <p className="text-[11px] text-neutral-500 mt-0.5 leading-snug">{g.hint}</p>
            <ul className="mt-2 flex flex-col gap-2">
              {g.items.map((m) => {
                const s = TIER_STYLES[m.tier];
                return (
                  <li
                    key={m.name}
                    className={`text-[12px] leading-snug rounded-lg border ${s.boxClass} px-2 py-2`}
                  >
                    <div className="flex items-baseline justify-between gap-2 flex-wrap">
                      <span className="font-semibold text-neutral-800">{m.name}</span>
                      <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${s.chipClass} shrink-0`}>
                        {s.badge}
                      </span>
                    </div>
                    {(m.unit || m.normal) && (
                      <div className="text-[10px] text-neutral-500 tabular-nums mt-0.5">
                        {m.unit ?? ''}
                        {m.unit && m.normal ? ' · ' : ''}
                        {m.normal ?? ''}
                      </div>
                    )}
                    <p className="text-neutral-700 mt-1">{m.meaning}</p>
                  </li>
                );
              })}
            </ul>
          </section>
        ))}
      </div>
    </aside>
  );
}
