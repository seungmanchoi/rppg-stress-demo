import type { CompositeBreakdown, StressComponent } from '@entities/measurement';
import { stressBand } from '@shared/lib/labels';
import { TIER_STYLES, type MetricTier } from '@shared/lib/metricTiers';

interface Props {
  title: string;
  subtitle: string;
  data: CompositeBreakdown;
}

export function StressBreakdown({ title, subtitle, data }: Props) {
  const band = stressBand(data.level);
  return (
    <div
      className="rounded-lg border px-3 py-2"
      style={{
        backgroundColor: `${band.color}14`,
        borderColor: `${band.color}55`,
      }}
    >
      <div className="flex items-baseline justify-between gap-2">
        <div className="min-w-0">
          <div className="text-[11px] uppercase tracking-wider font-semibold" style={{ color: band.color }}>
            {title}
          </div>
          <div className="text-[10px] text-neutral-500 leading-snug">{subtitle}</div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-lg font-bold tabular-nums" style={{ color: band.color }}>
            {Math.round(data.score)}
          </div>
          <div className="text-[10px] font-semibold" style={{ color: band.color }}>
            {band.label}
          </div>
        </div>
      </div>

      {data.components.length > 0 && (
        <ul className="mt-2 flex flex-col gap-1">
          {data.components.map((c: StressComponent) => {
            const tier = TIER_STYLES[c.tier as MetricTier] ?? TIER_STYLES.clinical;
            const widthPct = Math.min(100, c.contribution / (100 * c.weight) * 100);
            return (
              <li key={c.name} className="text-[10px] flex flex-col gap-0.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-1.5 min-w-0">
                    <span className={`font-mono px-1 py-px rounded text-[8px] ${tier.chipClass}`}>
                      {tier.badge[0]}
                    </span>
                    <span className="font-semibold text-neutral-700 truncate">{c.label}</span>
                    <span className="text-neutral-400 tabular-nums shrink-0">
                      · {c.rawValue.toFixed(c.rawValue >= 100 ? 0 : 2)} {c.rawUnit}
                    </span>
                  </span>
                  <span className="text-neutral-700 tabular-nums font-semibold shrink-0">
                    +{c.contribution.toFixed(1)}
                    <span className="text-neutral-400 font-normal"> / {(100 * c.weight).toFixed(0)}</span>
                  </span>
                </div>
                <div className="h-1 rounded-full bg-neutral-200 overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${widthPct}%`,
                      backgroundColor: band.color,
                      opacity: 0.5,
                    }}
                  />
                </div>
              </li>
            );
          })}
          <li className="text-[10px] text-neutral-500 text-right mt-0.5 tabular-nums">
            합계 = {data.components.reduce((s: number, c: StressComponent) => s + c.contribution, 0).toFixed(1)}{' '}
            (가중치 총합{' '}
            {(data.components.reduce((s: number, c: StressComponent) => s + c.weight, 0) * 100).toFixed(0)} %)
          </li>
        </ul>
      )}
    </div>
  );
}
