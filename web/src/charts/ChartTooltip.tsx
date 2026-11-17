import type { TooltipProps } from "recharts";

import { CHART } from "./chartTheme";

interface Props extends TooltipProps<number, string> {
  valueFormat: (v: number) => string;
  labelText?: (label: string) => string;
}

// A single tooltip style shared by every chart.
export function ChartTooltip({ active, payload, label, valueFormat, labelText }: Props) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-lg border border-border bg-surface px-3 py-2 shadow-card">
      <p className="mb-1 text-[11px] font-medium text-muted">
        {labelText ? labelText(String(label)) : String(label)}
      </p>
      {payload.map((p) => (
        <p key={String(p.name)} className="tnum text-[13px]" style={{ color: CHART.ink }}>
          {valueFormat(Number(p.value))}
        </p>
      ))}
    </div>
  );
}
