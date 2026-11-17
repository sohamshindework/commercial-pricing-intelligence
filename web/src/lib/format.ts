// Centralised numeric / currency / date formatting (presentation only).

const gbp0 = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  maximumFractionDigits: 0,
});

const gbp2 = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  maximumFractionDigits: 2,
});

const int0 = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 });

export const money = (v: number): string => gbp0.format(v);
export const money2 = (v: number): string => gbp2.format(v);
export const count = (v: number): string => int0.format(v);

export function moneyCompact(v: number): string {
  const abs = Math.abs(v);
  if (abs >= 1_000_000) return `${v < 0 ? "−" : ""}£${(abs / 1_000_000).toFixed(2)}m`;
  if (abs >= 1_000) return `${v < 0 ? "−" : ""}£${(abs / 1_000).toFixed(0)}k`;
  return money(v);
}

// Consistent axis unit (always millions) so ticks don't mix £..m and £..k.
export function moneyAxis(v: number): string {
  if (v === 0) return "£0";
  return `£${(v / 1_000_000).toFixed(1)}m`;
}

export const percent = (v: number, dp = 1): string => `${v.toFixed(dp)}%`;

export function signedPercent(v: number, dp = 1): string {
  const s = v > 0 ? "+" : "";
  return `${s}${v.toFixed(dp)}%`;
}
