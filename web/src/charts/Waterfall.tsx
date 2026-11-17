import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisTick, CHART } from "./chartTheme";

export interface WaterfallStep {
  label: string;
  value: number;
  kind: string; // "start" | "delta" | "end"
}

interface Row {
  label: string;
  base: number;
  bar: number;
  value: number;
  fill: string;
}

function toRows(steps: WaterfallStep[]): Row[] {
  let running = 0;
  const rows: Row[] = [];
  for (const s of steps) {
    if (s.kind === "start" || s.kind === "end") {
      running = s.kind === "start" ? s.value : running;
      rows.push({ label: s.label, base: 0, bar: s.value, value: s.value, fill: CHART.iris });
    } else if (s.value >= 0) {
      rows.push({ label: s.label, base: running, bar: s.value, value: s.value, fill: CHART.positive });
      running += s.value;
    } else {
      rows.push({
        label: s.label, base: running + s.value, bar: -s.value, value: s.value, fill: CHART.negative,
      });
      running += s.value;
    }
  }
  return rows;
}

interface Props {
  steps: WaterfallStep[];
  height?: number;
  valueFormat: (v: number) => string;
}

export function Waterfall({ steps, height = 300, valueFormat }: Props) {
  const rows = toRows(steps);
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart layout="vertical" data={rows} margin={{ left: 4, right: 16, top: 4, bottom: 4 }}>
        <XAxis
          type="number"
          tickFormatter={valueFormat}
          tick={axisTick}
          tickLine={false}
          axisLine={{ stroke: CHART.grid }}
        />
        <YAxis
          type="category"
          dataKey="label"
          width={132}
          tick={{ fontSize: 11, fill: CHART.body }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          cursor={{ fill: "rgba(101,83,163,0.06)" }}
          content={({ active, payload }) => {
            if (!active || !payload || !payload.length) return null;
            const row = payload[0].payload as Row;
            return (
              <div className="rounded-lg border border-border bg-surface px-3 py-2 shadow-card">
                <p className="mb-0.5 text-[11px] font-medium text-muted">{row.label}</p>
                <p className="tnum text-[13px] text-ink">{valueFormat(row.value)}</p>
              </div>
            );
          }}
        />
        <Bar dataKey="base" stackId="w" fill="transparent" />
        <Bar dataKey="bar" stackId="w" radius={[2, 2, 2, 2]} maxBarSize={22}>
          {rows.map((r) => (
            <Cell key={r.label} fill={r.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
