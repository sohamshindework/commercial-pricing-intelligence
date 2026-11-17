import type { ReactNode } from "react";

interface KpiCardProps {
  label: string;
  value: string;
  hint?: string;
  tone?: "default" | "positive" | "negative";
  children?: ReactNode;
}

const toneClass: Record<NonNullable<KpiCardProps["tone"]>, string> = {
  default: "text-ink",
  positive: "text-positive",
  negative: "text-negative",
};

export function KpiCard({ label, value, hint, tone = "default" }: KpiCardProps) {
  return (
    <div className="rounded-card border border-border bg-surface p-4 shadow-card">
      <p className="text-[13px] font-medium text-muted">{label}</p>
      <p className={`mt-1 font-heading text-kpi tnum ${toneClass[tone]}`}>{value}</p>
      {hint && <p className="mt-1 text-[12px] text-muted">{hint}</p>}
    </div>
  );
}
