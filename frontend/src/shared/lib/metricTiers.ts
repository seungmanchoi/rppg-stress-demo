/**
 * 측정 지표를 신뢰도 등급(tier)별로 분류.
 *
 * - `clinical`: ESC/NASPE 1996 Task Force, ANSI/AAMI 등 임상 표준
 * - `commercial`: Kubios HRV, HeartMath emWave, Polar 등 상용 제품에서 사용
 * - `research`: 다수 논문 검증, 학계 표준 비선형 지표
 * - `experimental`: 연구 단계 / rPPG 추출 정확도 변동성
 * - `rgbEstimated`: RGB 카메라만으로 추정 — 의료기기 대비 정확도 한계 명시
 */
export type MetricTier = 'clinical' | 'commercial' | 'research' | 'experimental' | 'rgbEstimated';

export interface TierStyle {
  label: string;
  badge: string;
  meaning: string;
  /** Tailwind className for box border/background */
  boxClass: string;
  /** Tailwind className for badge chip */
  chipClass: string;
}

export const TIER_STYLES: Record<MetricTier, TierStyle> = {
  clinical: {
    label: '임상 표준',
    badge: 'CLINICAL',
    meaning: 'ESC/NASPE 1996 등 임상 가이드라인 표준 지표',
    boxClass: 'border-emerald-300 bg-emerald-50/60',
    chipClass: 'bg-emerald-100 text-emerald-800 border border-emerald-300',
  },
  commercial: {
    label: '상용 표준',
    badge: 'COMMERCIAL',
    meaning: 'Kubios · HeartMath · Polar 등 상용 제품에서 채택',
    boxClass: 'border-sky-300 bg-sky-50/60',
    chipClass: 'bg-sky-100 text-sky-800 border border-sky-300',
  },
  research: {
    label: '학계 검증',
    badge: 'RESEARCH',
    meaning: '다수 논문 검증 — 비선형 / 엔트로피 / 프랙탈',
    boxClass: 'border-violet-300 bg-violet-50/60',
    chipClass: 'bg-violet-100 text-violet-800 border border-violet-300',
  },
  experimental: {
    label: '실험적',
    badge: 'EXPERIMENTAL',
    meaning: 'rPPG로 추출 가능하지만 정확도 변동 — 참고용',
    boxClass: 'border-amber-300 bg-amber-50/60',
    chipClass: 'bg-amber-100 text-amber-800 border border-amber-300',
  },
  rgbEstimated: {
    label: 'RGB 추정',
    badge: 'RGB-ESTIMATED',
    meaning: 'RGB 카메라만으로 추정 — 의료기기 대비 큰 오차 가능',
    boxClass: 'border-rose-300 bg-rose-50/60',
    chipClass: 'bg-rose-100 text-rose-800 border border-rose-300',
  },
};

export const TIER_ORDER: MetricTier[] = [
  'clinical',
  'commercial',
  'research',
  'experimental',
  'rgbEstimated',
];
