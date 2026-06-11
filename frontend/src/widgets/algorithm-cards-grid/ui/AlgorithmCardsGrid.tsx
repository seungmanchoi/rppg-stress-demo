import type { AlgorithmResult } from '@entities/measurement';

import { AlgorithmResultCard } from '@features/algorithm-result-card/ui/AlgorithmResultCard';

export function AlgorithmCardsGrid({ results }: { results: AlgorithmResult[] }) {
  const sorted = [...results].sort((a, b) => {
    if (a.available !== b.available) return a.available ? -1 : 1;
    const ar = a.reliability?.score ?? 0;
    const br = b.reliability?.score ?? 0;
    return br - ar;
  });
  const availableCount = sorted.filter((r) => r.available).length;
  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-baseline justify-between">
        <h2 className="font-semibold text-base">적용 알고리즘</h2>
        <span className="text-xs text-neutral-500">
          {availableCount} / {sorted.length}개 사용 가능
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {sorted.map((r) => (
          <AlgorithmResultCard key={r.meta.id} result={r} />
        ))}
      </div>
    </section>
  );
}
