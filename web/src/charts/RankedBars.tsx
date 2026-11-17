import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisTick, CHART } from "./chartTheme";

export interface RankedDatum {
  label: string;
  value: number;
  color?: string;
  meta?: string; // optional secondary line in the tooltip (e.g. share, support)
}

interface Props {
  data: RankedDatum[];
  height?: number;
  color?: string;
  valueFormat: (v: number) => string;
  axisFormat: (v: number) => string;
  labelWidth?: number;
}

export function RankedBars({
  data,
  height = 320,
  color = CHART.iris,
  valueFormat,
  axisFormat,
  labelWidth = 150,
}: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart layout="vertical" data={data} margin={{ left: 4, right: 16, top: 4, bottom: 4 }}>
        <XAxis
          type="number"
          tickFormatter={axisFormat}
          tick={axisTick}
          tickLine={false}
          axisLine={{ stroke: CHART.grid }}
        />
        <YAxis
          type="category"
          dataKey="label"
          width={labelWidth}
          tick={{ fontSize: 11.5, fill: CHART.body }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          cursor={{ fill: "rgba(101,83,163,0.06)" }}
          content={({ active, payload }) => {
            if (!active || !payload || !payload.length) return null;
            const d = payload[0].payload as RankedDatum;
            return (
              <div className="rounded-lg border border-border bg-surface px-3 py-2 shadow-card">
                <p className="mb-0.5 text-[11px] font-medium text-muted">{d.label}</p>
                <p className="tnum text-[13px] text-ink">{valueFormat(d.value)}</p>
                {d.meta && <p className="mt-0.5 text-[11.5px] text-muted">{d.meta}</p>}
              </div>
            );
          }}
        />
        <Bar dataKey="value" radius={[0, 3, 3, 0]} maxBarSize={26}>
          {data.map((d) => (
            <Cell key={d.label} fill={d.color ?? color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
