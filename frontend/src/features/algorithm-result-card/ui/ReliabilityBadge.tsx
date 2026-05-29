import type { ReliabilityGrade } from '@entities/measurement';
import { RELIABILITY_BANDS } from '@shared/lib/labels';

const STYLES: Record<ReliabilityGrade, string> = {
  high: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  medium: 'bg-amber-100 text-amber-800 border-amber-200',
  low: 'bg-rose-100 text-rose-800 border-rose-200',
};

export function ReliabilityBadge({ grade, score }: { grade: ReliabilityGrade; score: number }) {
  const info = RELIABILITY_BANDS[grade];
  return (
    <span
      className={`text-xs px-2 py-1 rounded-full font-semibold border ${STYLES[grade]}`}
      title={info.description}
    >
      신뢰도 {info.label} · {Math.round(score)}
    </span>
  );
}
