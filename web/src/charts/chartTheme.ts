// Shared chart tokens so every visualization reads as one system.
// Semantic colors are consistent: positive = growth, negative = decline,
// coral = commercial opportunity, sage = customer/retention, lilac = comparison.

export const CHART = {
  ink: "#2F2941",
  body: "#51495F",
  muted: "#777184",
  grid: "#E8E1E8",
  iris: "#6653A3",
  lilac: "#C5B6E1",
  coral: "#DC8B73",
  sage: "#91ADAA",
  positive: "#437F72",
  negative: "#B75B68",
} as const;

// Categorical sequence for multi-series / multi-category charts.
export const CATEGORICAL = [
  CHART.iris,
  CHART.sage,
  CHART.coral,
  CHART.lilac,
  "#8E7FB8",
  "#B6926F",
  "#7FA39E",
  "#A99ACB",
] as const;

export const axisTick = { fontSize: 11, fill: CHART.muted } as const;
export const axisLine = { stroke: CHART.grid } as const;
