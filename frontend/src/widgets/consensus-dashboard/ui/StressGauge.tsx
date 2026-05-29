import { RadialBar, RadialBarChart, ResponsiveContainer } from 'recharts';

import type { StressLevel } from '@entities/measurement';

const COLOR_FOR: Record<StressLevel, string> = {
  low: '#10b981',
  mid: '#f59e0b',
  high: '#ef4444',
  very_high: '#7c1d1d',
};

const LABEL_FOR: Record<StressLevel, string> = {
  low: '낮음',
  mid: '보통',
  high: '높음',
  very_high: '매우 높음',
};

export function StressGauge({ score, level }: { score: number; level: StressLevel }) {
  const data = [{ name: 's', value: Math.max(0, Math.min(100, score)), fill: COLOR_FOR[level] }];
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
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
        <span className="text-3xl font-bold">{Math.round(score)}</span>
        <span className="text-[10px] uppercase text-neutral-500 tracking-wider mt-1">STRESS</span>
        <span className="text-xs font-semibold mt-1" style={{ color: COLOR_FOR[level] }}>
          {LABEL_FOR[level]}
        </span>
      </div>
    </div>
  );
}
