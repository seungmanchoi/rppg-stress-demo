export function MetricRow({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex justify-between items-baseline">
      <span className="text-neutral-500">{label}</span>
      <span className={highlight ? 'font-semibold text-neutral-900' : 'text-neutral-800'}>{value}</span>
    </div>
  );
}
