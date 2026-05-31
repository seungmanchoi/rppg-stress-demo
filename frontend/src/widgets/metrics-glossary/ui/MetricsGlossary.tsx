interface MetricEntry {
  name: string;
  unit?: string;
  normal?: string;
  meaning: string;
}

interface MetricGroup {
  title: string;
  hint: string;
  items: MetricEntry[];
}

const GROUPS: MetricGroup[] = [
  {
    title: 'HRV — 자율신경 지표',
    hint: '심장 박동 간격(IBI)의 변동에서 추출. 임상 HRV 표준 (ESC/NASPE 1996).',
    items: [
      {
        name: '심박수 (HR)',
        unit: 'BPM',
        normal: '안정 시 60~100',
        meaning: '분당 박동 수. 60,000 ÷ 평균 IBI(ms).',
      },
      {
        name: 'RMSSD',
        unit: 'ms',
        normal: '20~80 (이완 시 100+)',
        meaning: '연속한 두 박동 간격 차이의 RMS. 부교감 활성(이완) 표준 지표. 클수록 신경 유연.',
      },
      {
        name: 'LF/HF',
        unit: '비율',
        normal: '0.5~2.0 (≈1.0 균형)',
        meaning: 'IBI의 저주파(교감 우세) / 고주파(부교감 우세) 파워 비율. 높으면 긴장.',
      },
      {
        name: 'Baevsky SI',
        unit: '점수',
        normal: '50~150 정상',
        meaning:
          '러시아 우주의학에서 만든 자율신경 경직도 지수. 박동 간격이 좁은 구간에 몰릴수록 ↑. 150~500 약한 긴장, 500+ 고스트레스.',
      },
    ],
  },
  {
    title: '스트레스 점수',
    hint: '본 데모가 위 세 지표를 4:4:2로 가중합한 합성 지표. 임상 표준 아님.',
    items: [
      {
        name: '스트레스 점수',
        unit: '0~100',
        normal: '구간별 라벨 참조',
        meaning:
          'norm_baev × 0.4 + norm_lfhf × 0.4 + norm_rmssd × 0.2. 0~30 낮음, 30~60 보통, 60~80 높음, 80+ 매우 높음.',
      },
    ],
  },
  {
    title: '신뢰도 점수 + 4개 구성 성분',
    hint: '각 알고리즘 결과를 얼마나 믿을지. 30 미만이면 합의에서 자동 제외.',
    items: [
      {
        name: '신호품질 (SNR)',
        unit: 'dB',
        normal: '−5 ~ +10',
        meaning: 'BVP 신호 대 잡음비. 0 dB = 신호와 잡음이 같음, 클수록 깨끗. 가중치 30%.',
      },
      {
        name: '얼굴 추적',
        unit: '%',
        normal: '95% 이상',
        meaning: '30초 영상 중 얼굴이 검출된 프레임 비율. 가중치 25%.',
      },
      {
        name: 'HR 편차',
        unit: 'BPM',
        normal: '±5 이내',
        meaning: '8개 알고리즘 HR 중앙값과의 차이. 가중치 25%. ±25 BPM 초과 시 자동 강등.',
      },
      {
        name: '움직임',
        unit: 'px',
        normal: '2 미만',
        meaning: '프레임 간 평균 픽셀 이동량. 머리 / 표정 변화. 가중치 20%.',
      },
    ],
  },
  {
    title: '합의 (Consensus)',
    hint: '8개 카드 결과를 신뢰도 가중 median으로 모아 최종 점수 산출.',
    items: [
      {
        name: '합의 가중치',
        unit: '0~70',
        meaning: 'max(신뢰도 − 30, 0). 신뢰도 30 미만이면 0 = 합의 제외. 75+ 카드는 가중치 45+.',
      },
      {
        name: '기여 알고리즘 수',
        unit: '카드 / 8',
        meaning: '실제 합의에 들어간 가용 카드 수. unavailable은 제외.',
      },
    ],
  },
];

export function MetricsGlossary() {
  return (
    <aside className="rounded-3xl bg-white border p-5 shadow-sm flex flex-col gap-4">
      <header>
        <h2 className="font-semibold text-base">측정 지표 안내</h2>
        <p className="text-xs text-neutral-500 mt-0.5">
          각 카드와 합의 대시보드에 표시되는 모든 수치의 의미와 정상 범위입니다.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {GROUPS.map((g) => (
          <section
            key={g.title}
            className="rounded-2xl border border-neutral-200 bg-neutral-50/50 p-3"
          >
            <h3 className="text-sm font-semibold text-neutral-800">{g.title}</h3>
            <p className="text-[11px] text-neutral-500 mt-0.5 leading-snug">{g.hint}</p>
            <ul className="mt-2 flex flex-col gap-2">
              {g.items.map((m) => (
                <li
                  key={m.name}
                  className="text-[12px] leading-snug border-t border-neutral-200 pt-2 first:border-t-0 first:pt-0"
                >
                  <div className="flex items-baseline justify-between gap-2 flex-wrap">
                    <span className="font-semibold text-neutral-800">{m.name}</span>
                    <span className="text-[10px] text-neutral-400 tabular-nums shrink-0">
                      {m.unit ? `${m.unit}` : ''}
                      {m.unit && m.normal ? ' · ' : ''}
                      {m.normal ?? ''}
                    </span>
                  </div>
                  <p className="text-neutral-600 mt-0.5">{m.meaning}</p>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </aside>
  );
}
