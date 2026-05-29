import { Line, LineChart, ResponsiveContainer } from 'recharts';

export function BvpSparkline({ data }: { data: number[] }) {
  if (!data?.length) {
    return <div className="h-12 flex items-center justify-center text-xs text-neutral-400">신호 없음</div>;
  }
  const points = data.map((v, i) => ({ i, v }));
  return (
    <div className="h-12">
      <ResponsiveContainer>
        <LineChart data={points} margin={{ top: 2, right: 0, bottom: 2, left: 0 }}>
          <Line type="monotone" dataKey="v" stroke="#0ea5e9" strokeWidth={1.5} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
