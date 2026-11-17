import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { axisTick, CHART } from "./chartTheme";
import { ChartTooltip } from "./ChartTooltip";

interface TrendPointLike {
  label: string;
  value: number;
}

interface Props {
  data: TrendPointLike[];
  height?: number;
  valueFormat: (v: number) => string;
  axisFormat: (v: number) => string;
  labelText?: (label: string) => string;
}

export function TrendLine({ data, height = 320, valueFormat, axisFormat, labelText }: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ left: 4, right: 12, top: 8, bottom: 4 }}>
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={CHART.iris} stopOpacity={0.16} />
            <stop offset="100%" stopColor={CHART.iris} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={CHART.grid} vertical={false} />
        <XAxis
          dataKey="label"
          tick={axisTick}
          tickLine={false}
          axisLine={{ stroke: CHART.grid }}
          minTickGap={28}
        />
        <YAxis
          tickFormatter={axisFormat}
          tick={axisTick}
          tickLine={false}
          axisLine={false}
          width={52}
        />
        <Tooltip
          cursor={{ stroke: CHART.lilac, strokeWidth: 1 }}
          content={<ChartTooltip valueFormat={valueFormat} labelText={labelText} />}
        />
        <Area
          type="monotone"
          dataKey="value"
          stroke={CHART.iris}
          strokeWidth={2.25}
          fill="url(#trendFill)"
          dot={false}
          activeDot={{ r: 4, fill: CHART.iris, stroke: "#fff", strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
