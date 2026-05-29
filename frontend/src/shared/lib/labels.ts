import type {
  BaevskyLevel,
  ReliabilityGrade,
  StressLevel,
} from '@entities/measurement';

export interface StressBand {
  level: StressLevel;
  min: number;
  max: number;
  label: string;       // 짧은 이름  e.g. "보통"
  full: string;        // 풀어쓴 표현 e.g. "보통 — 약한 긴장 상태"
  description: string; // 한 줄 의미 설명
  color: string;       // gauge / badge용
}

export const STRESS_BANDS: StressBand[] = [
  {
    level: 'low',
    min: 0,
    max: 30,
    label: '낮음',
    full: '낮음 — 이완 상태',
    description: '부교감 신경이 우세, 휴식 / 회복 단계입니다.',
    color: '#10b981',
  },
  {
    level: 'mid',
    min: 30,
    max: 60,
    label: '보통',
    full: '보통 — 약한 긴장',
    description: '교감·부교감이 균형 잡힌 일상 상태입니다.',
    color: '#f59e0b',
  },
  {
    level: 'high',
    min: 60,
    max: 80,
    label: '높음',
    full: '높음 — 스트레스 상승',
    description: '교감 신경이 우세, 지속되면 회복 시간이 필요합니다.',
    color: '#ef4444',
  },
  {
    level: 'very_high',
    min: 80,
    max: 100,
    label: '매우 높음',
    full: '매우 높음 — 자율신경 불균형',
    description: '강한 스트레스 / 탈진 신호. 휴식과 회복 활동을 권장합니다.',
    color: '#7c1d1d',
  },
];

const _STRESS_BY_LEVEL: Record<StressLevel, StressBand> = Object.fromEntries(
  STRESS_BANDS.map((b) => [b.level, b]),
) as Record<StressLevel, StressBand>;

export function stressBand(level: StressLevel): StressBand {
  return _STRESS_BY_LEVEL[level];
}

export const RELIABILITY_BANDS: Record<
  ReliabilityGrade,
  { label: string; full: string; description: string }
> = {
  high: {
    label: '높음',
    full: '신뢰도 높음',
    description: '신호 / 트래킹 / 알고리즘 합의 모두 양호',
  },
  medium: {
    label: '보통',
    full: '신뢰도 보통',
    description: '대체로 신뢰 가능하나 일부 잡음 / 편차 존재',
  },
  low: {
    label: '낮음',
    full: '신뢰도 낮음',
    description: '신호 부족 — 결과를 합의에서 제외하거나 가볍게 참고',
  },
};

export const BAEVSKY_BANDS: Record<
  BaevskyLevel,
  { label: string; range: string }
> = {
  normal: { label: '정상', range: '50–150' },
  mild: { label: '약한 긴장', range: '150–500' },
  moderate: { label: '중등도 스트레스', range: '500–900' },
  high: { label: '고스트레스', range: '> 900' },
};
