import { RadialBar, RadialBarChart, ResponsiveContainer } from 'recharts';

import type { StressLevel } from '@entities/measurement';
import { stressBand } from '@shared/lib/labels';

export function StressGauge({ score, level }: { score: number; level: StressLevel }) {
  const band = stressBand(level);
  const data = [{ name: 's', value: Math.max(0, Math.min(100, score)), fill: band.color }];
  return (
    <div className="relative h-40 w-40 shrink-0">
      <ResponsiveContainer>
        <RadialBarChart
          innerRadius="70%"
          outerRadius="100%"
          startAngle={90}
          endAngle={-270}
          data={data}
        >
          <RadialBar background dataKey="value" cornerRadius={10} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none px-2">
        <span className="text-3xl font-bold">{Math.round(score)}</span>
        <span className="text-[10px] uppercase text-neutral-500 tracking-wider mt-1">
          STRESS / 100
        </span>
        <span className="text-xs font-semibold mt-1" style={{ color: band.color }}>
          {band.label}
        </span>
      </div>
    </div>
  );
}
