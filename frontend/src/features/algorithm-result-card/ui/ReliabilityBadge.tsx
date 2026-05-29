import type { ReliabilityGrade } from '@entities/measurement';

const STYLES: Record<ReliabilityGrade, string> = {
  high: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  medium: 'bg-amber-100 text-amber-800 border-amber-200',
  low: 'bg-rose-100 text-rose-800 border-rose-200',
};

export function ReliabilityBadge({ grade, score }: { grade: ReliabilityGrade; score: number }) {
  return (
    <span className={`text-xs px-2 py-1 rounded-full font-semibold border ${STYLES[grade]}`}>
      {grade.toUpperCase()} {Math.round(score)}
    </span>
  );
}
