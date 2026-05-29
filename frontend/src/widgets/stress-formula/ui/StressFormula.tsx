/**
 * "스트레스 지수가 어떻게 만들어지는가" — 일반인용 풀어쓰기 패널.
 * 정확한 수식은 docs/specs/2026-05-29-rppg-stress-demo-design.md §7 참고.
 */
import { STRESS_BANDS } from '@shared/lib/labels';

interface Step {
  num: string;
  title: string;
  paragraphs: string[];
  bullets?: { term: string; meaning: string }[];
}

const STEPS: Step[] = [
  {
    num: '1',
    title: '맥파에서 심장 박동 간격을 뽑아냅니다',
    paragraphs: [
      '얼굴 영상에서 추출한 미세한 색 변화(맥파)에서, 심장이 한 번 뛸 때 생기는 봉우리를 하나하나 찾아냅니다.',
      '봉우리와 봉우리 사이의 시간 간격(밀리초 단위)이 곧 "이번 박동에 걸린 시간"이고, 이 숫자들의 시계열이 모든 분석의 출발점입니다.',
      '튀는 값(예: 갑자기 두 배로 늘어난 간격)은 잡음으로 보고 자동으로 제외합니다.',
    ],
  },
  {
    num: '2',
    title: '심박 간격에서 자율신경 상태를 읽어냅니다',
    paragraphs: [
      '심장은 항상 같은 간격으로 뛰지 않습니다. 매번 미세하게 흔들리는데, 이 흔들림 패턴이 자율신경(교감·부교감)의 상태를 보여줍니다.',
      '편안할수록 흔들림이 크고 유연하며, 긴장할수록 박동 간격이 일정하게 굳어집니다. 아래 지표들을 모두 함께 봅니다.',
    ],
    bullets: [
      {
        term: '전체 흔들림 (SDNN)',
        meaning: '측정 시간 동안 심장 박동 간격이 얼마나 들쭉날쭉했는지. 자율신경이 건강할수록 적당히 큽니다.',
      },
      {
        term: '짧은 흔들림 (RMSSD)',
        meaning: '바로 다음 박동과 비교했을 때의 흔들림. 편안할 때 크게 흔들리고, 긴장하면 줄어듭니다. (부교감 활성)',
      },
      {
        term: '큰 변동 비율 (pNN50)',
        meaning: '연속한 두 박동 간격 차이가 50ms 넘는 비율. 클수록 신경이 유연합니다.',
      },
      {
        term: '긴장 / 휴식 균형 (LF/HF)',
        meaning: '느린 변동(긴장 모드, 교감)과 빠른 변동(휴식 모드, 부교감)의 비율. 1 근처면 균형, 높을수록 긴장 우세.',
      },
    ],
  },
  {
    num: '3',
    title: '자율신경 경직도를 점수로 만듭니다 (Baevsky Index)',
    paragraphs: [
      '박동 간격이 항상 같은 값 근처에만 머무를수록 "자율신경이 굳어져 있다"고 봅니다. 반대로 박동 간격이 폭넓게 변동하면 "신경이 유연하다"고 봅니다.',
      '러시아 우주의학에서 우주비행사의 스트레스 상태를 측정하던 방식이며, 지금도 임상에서 자율신경 긴장도의 표준 지표 중 하나입니다.',
    ],
    bullets: [
      { term: '50 ~ 150', meaning: '정상 — 자율신경이 편안하게 작동' },
      { term: '150 ~ 500', meaning: '약한 긴장 — 일상적 스트레스 범위' },
      { term: '500 ~ 900', meaning: '중등도 스트레스 — 회복이 필요' },
      { term: '900 이상', meaning: '고스트레스 — 자율신경 부담 큼' },
    ],
  },
  {
    num: '4',
    title: '세 지표를 합쳐 0~100 스트레스 점수를 만듭니다',
    paragraphs: [
      '지금까지 본 세 가지 — 자율신경 경직도, 긴장/휴식 균형, 짧은 흔들림 — 를 각각 0에서 1 사이 값으로 환산한 뒤, 4 : 4 : 2 비율로 섞어 100점 만점 점수를 만듭니다.',
      '경직도와 긴장/휴식 균형은 동등하게 가장 중요하게 보고, 짧은 흔들림은 보조 지표로 사용합니다.',
      '점수가 높을수록 스트레스 상태에 가깝습니다. 구간 의미는 오른쪽 "스트레스 구간 안내" 패널과 같습니다.',
    ],
    bullets: STRESS_BANDS.map((b) => ({
      term: `${b.min} ~ ${b.max}`,
      meaning: b.full + ' — ' + b.description,
    })),
  },
  {
    num: '5',
    title: '각 결과가 얼마나 믿을 만한지 신뢰도를 계산합니다',
    paragraphs: [
      '같은 영상이라도 알고리즘마다 결과가 조금씩 다릅니다. 모든 결과를 똑같이 믿지 않고, 다음 네 가지를 보고 0~100점의 신뢰도를 매깁니다.',
    ],
    bullets: [
      { term: '신호가 깨끗한가', meaning: '맥파가 노이즈에 비해 얼마나 또렷한지 (SNR)' },
      { term: '얼굴이 잘 잡혔는가', meaning: '측정 시간 동안 얼굴이 인식된 비율' },
      { term: '많이 움직였는가', meaning: '머리 / 표정 움직임이 적을수록 점수가 높습니다' },
      { term: '다른 알고리즘과 비슷한가', meaning: '8개 알고리즘끼리 심박수가 일치할수록 점수가 높습니다' },
    ],
  },
  {
    num: '6',
    title: '8개 알고리즘 결과를 신뢰도 기준으로 모아 최종 점수를 냅니다',
    paragraphs: [
      '8개 카드를 그냥 평균 내지 않습니다. 신뢰도가 낮은(보통 미만) 카드의 결과는 합의에서 제외하고, 신뢰도가 높을수록 무게를 더 주어 중앙값으로 모읍니다.',
      '이렇게 하면 한두 알고리즘이 이상한 값을 내더라도 다수가 일관되게 가리키는 값이 최종 점수가 됩니다. 상단 게이지에 표시되는 숫자가 바로 이 합의 점수입니다.',
    ],
  },
];

export function StressFormula() {
  return (
    <details className="rounded-2xl bg-white border p-5 shadow-sm group">
      <summary className="cursor-pointer flex items-center justify-between font-semibold text-base">
        <span>스트레스 지수는 이렇게 계산됩니다</span>
        <span className="text-neutral-400 group-open:rotate-180 transition-transform">⌄</span>
      </summary>

      <p className="text-sm text-neutral-600 mt-3 leading-relaxed">
        얼굴 영상에서 심장의 미세한 움직임을 읽어내 자율신경 상태를 추정합니다. 아래 6단계를 거쳐
        100점 만점 스트레스 점수가 만들어집니다.
      </p>

      <ol className="mt-5 space-y-5">
        {STEPS.map((s) => (
          <li key={s.num} className="flex gap-4">
            <div className="shrink-0 w-8 h-8 rounded-full bg-sky-500 text-white flex items-center justify-center text-sm font-semibold">
              {s.num}
            </div>
            <div className="flex-1 min-w-0 space-y-2">
              <h4 className="font-semibold text-neutral-800 text-sm leading-snug">{s.title}</h4>
              {s.paragraphs.map((p, idx) => (
                <p key={idx} className="text-sm text-neutral-600 leading-relaxed">
                  {p}
                </p>
              ))}
              {s.bullets && (
                <ul className="mt-2 space-y-1 border-l-2 border-neutral-100 pl-3">
                  {s.bullets.map((b) => (
                    <li key={b.term} className="text-xs">
                      <span className="font-semibold text-neutral-800">{b.term}</span>
                      <span className="text-neutral-500"> — {b.meaning}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </li>
        ))}
      </ol>

      <p className="mt-6 text-[11px] text-neutral-400 italic border-t pt-3">
        ⚠ 본 데모는 의료기기가 아닙니다. 결과는 교육 / 연구용 추정치이며 진단·치료에 사용할 수
        없습니다.
      </p>
    </details>
  );
}
