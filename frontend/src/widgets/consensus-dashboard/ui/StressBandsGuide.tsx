import type { StressLevel } from '@entities/measurement';
import { STRESS_BANDS } from '@shared/lib/labels';

export function StressBandsGuide({ currentLevel }: { currentLevel?: StressLevel }) {
  return (
    <aside
      aria-label="스트레스 지수 구간 가이드"
      className="rounded-2xl border bg-white p-4 shadow-sm w-full md:max-w-xs flex flex-col gap-2"
    >
      <header className="flex items-baseline justify-between">
        <h3 className="text-sm font-semibold">스트레스 구간 안내</h3>
        <span className="text-[10px] text-neutral-400">0~100 composite score</span>
      </header>
      <ul className="flex flex-col gap-1.5">
        {STRESS_BANDS.map((b) => {
          const active = b.level === currentLevel;
          return (
            <li
              key={b.level}
              className={`flex items-start gap-2 rounded-lg px-2 py-1.5 transition-colors ${
                active ? 'bg-neutral-50 ring-1 ring-neutral-200' : ''
              }`}
            >
              <span
                className="mt-1 inline-block w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: b.color }}
                aria-hidden
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 text-xs">
                  <span
                    className={`font-mono tabular-nums text-neutral-600 ${
                      active ? 'font-semibold text-neutral-900' : ''
                    }`}
                  >
                    {b.min.toString().padStart(2, ' ')}–{b.max}
                  </span>
                  <span className={`font-semibold ${active ? '' : 'text-neutral-700'}`}>
                    {b.full}
                  </span>
                </div>
                <p className="text-[11px] text-neutral-500 leading-snug mt-0.5">
                  {b.description}
                </p>
              </div>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
