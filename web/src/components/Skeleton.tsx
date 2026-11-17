// Subtle loading placeholders (respect reduced motion via Tailwind's animate-pulse).

export function ChartSkeleton({ height = 300 }: { height?: number }) {
  return (
    <div className="animate-pulse" style={{ height }} aria-hidden>
      <div className="flex h-full items-end gap-3 px-2">
        {[50, 72, 40, 86, 60, 94, 48, 68].map((h, i) => (
          <div
            key={i}
            className="flex-1 rounded-t bg-surface-alt"
            style={{ height: `${h}%` }}
          />
        ))}
      </div>
    </div>
  );
}

export function BarsSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="animate-pulse space-y-3 py-2" aria-hidden>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="h-3 w-24 rounded bg-surface-alt" />
          <div className="h-5 rounded bg-surface-alt" style={{ width: `${90 - i * 9}%` }} />
        </div>
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="animate-pulse space-y-2.5" aria-hidden>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-7 rounded bg-surface-alt" />
      ))}
    </div>
  );
}
