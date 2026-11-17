// Loading, empty and error states (used by every data view).

export function Loading({ label = "Loading analysis…" }: { label?: string }) {
  return (
    <div
      role="status"
      className="flex items-center gap-3 rounded-card border border-border bg-surface px-4 py-6 text-sm text-muted"
    >
      <span className="h-2 w-2 animate-pulse rounded-full bg-iris" aria-hidden />
      {label}
    </div>
  );
}

export function EmptyState({ title, detail }: { title: string; detail?: string }) {
  return (
    <div className="rounded-card border border-dashed border-border bg-surface px-4 py-8 text-center">
      <p className="font-heading text-ink">{title}</p>
      {detail && <p className="mt-1 text-sm text-muted">{detail}</p>}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="rounded-card border border-negative/30 bg-negative/5 px-4 py-5 text-sm text-negative"
    >
      {message}
    </div>
  );
}
