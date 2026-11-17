// A deliberate metric hierarchy: one primary figure, a few supporting, the rest compact.

interface Tone {
  tone?: "default" | "positive" | "negative";
}

const toneClass: Record<NonNullable<Tone["tone"]>, string> = {
  default: "text-ink",
  positive: "text-positive",
  negative: "text-negative",
};

export function PrimaryStat({
  label,
  value,
  sub,
  subTone = "default",
}: {
  label: string;
  value: string;
  sub?: string;
  subTone?: NonNullable<Tone["tone"]>;
}) {
  return (
    <div>
      <p className="text-[12.5px] font-medium uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1 font-heading text-[40px] leading-none tnum text-ink">{value}</p>
      {sub && <p className={`mt-2 text-[13px] tnum ${toneClass[subTone]}`}>{sub}</p>}
    </div>
  );
}

export function SupportingStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[12.5px] font-medium text-muted">{label}</p>
      <p className="mt-1 font-heading text-[24px] leading-none tnum text-ink">{value}</p>
    </div>
  );
}

export function CompactStat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-border py-2.5 last:border-0">
      <span className="text-[13px] text-body">
        {label}
        {hint && <span className="ml-1 text-[11.5px] text-muted">{hint}</span>}
      </span>
      <span className="font-heading text-[16px] tnum text-ink">{value}</span>
    </div>
  );
}
