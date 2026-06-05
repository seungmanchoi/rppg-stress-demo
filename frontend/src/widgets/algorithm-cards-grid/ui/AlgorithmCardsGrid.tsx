import type { AlgorithmResult } from '@entities/measurement';

import { AlgorithmResultCard } from '@features/algorithm-result-card/ui/AlgorithmResultCard';

export function AlgorithmCardsGrid({ results }: { results: AlgorithmResult[] }) {
  const sorted = [...results].sort((a, b) => {
    if (a.available !== b.available) return a.available ? -1 : 1;
    const ar = a.reliability?.score ?? 0;
    const br = b.reliability?.score ?? 0;
    return br - ar;
  });
  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {sorted.map((r) => (
        <AlgorithmResultCard key={r.meta.id} result={r} />
      ))}
    </section>
  );
}
