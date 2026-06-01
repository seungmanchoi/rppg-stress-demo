import { TIER_ORDER, TIER_STYLES } from '@shared/lib/metricTiers';

/** 카드 그리드 바로 위에 두는 한 줄 컴팩트 범례. */
export function TierLegend() {
  return (
    <section className="rounded-2xl border bg-white p-3 shadow-sm">
      <div className="flex items-baseline justify-between mb-2">
        <h3 className="text-xs uppercase tracking-wider text-neutral-600 font-semibold">
          박스 색상 = 지표 신뢰도 등급
        </h3>
        <span className="text-[10px] text-neutral-400">자세한 설명은 페이지 하단 용어집</span>
      </div>
      <ul className="flex flex-wrap gap-2">
        {TIER_ORDER.map((tier) => {
          const s = TIER_STYLES[tier];
          return (
            <li
              key={tier}
              className={`flex items-center gap-2 rounded-lg border ${s.boxClass} px-2.5 py-1.5`}
            >
              <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${s.chipClass}`}>
                {s.badge}
              </span>
              <span className="text-[11px] font-semibold text-neutral-800 whitespace-nowrap">
                {s.label}
              </span>
              <span className="text-[10px] text-neutral-500 whitespace-nowrap hidden md:inline">
                · {s.meaning}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
