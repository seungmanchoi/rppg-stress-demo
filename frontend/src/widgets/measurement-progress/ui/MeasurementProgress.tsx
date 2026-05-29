export function MeasurementProgress({
  progress,
  stage,
  status,
}: {
  progress: number;
  stage: string;
  status: string;
}) {
  return (
    <div className="rounded-2xl bg-white border p-5 flex flex-col gap-2 shadow-sm">
      <div className="flex justify-between text-sm">
        <span className="text-neutral-600">
          {status === 'queued' ? '대기 중' : stage || '처리 중'}
        </span>
        <span className="font-semibold text-neutral-800">{(progress * 100).toFixed(0)}%</span>
      </div>
      <div className="h-2 bg-neutral-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-sky-500 transition-all duration-300"
          style={{ width: `${Math.max(2, progress * 100)}%` }}
        />
      </div>
    </div>
  );
}
