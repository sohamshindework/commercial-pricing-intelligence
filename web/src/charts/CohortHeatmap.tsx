import type { CohortRow } from "../api/types";

// Light lilac -> deep iris scale; offset 0 (100%) is the darkest.
const FROM = [239, 233, 245];
const TO = [74, 59, 125];

function cellColor(rate: number): string {
  const t = Math.max(0, Math.min(1, rate / 0.5)); // saturate at 50% retention
  const c = FROM.map((f, i) => Math.round(f + (TO[i] - f) * t));
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

function textColor(rate: number): string {
  return rate / 0.5 > 0.55 ? "#FFFFFF" : "#51495F";
}

interface Props {
  offsets: number[];
  cohorts: CohortRow[];
  maxOffset?: number;
}

export function CohortHeatmap({ offsets, cohorts, maxOffset = 12 }: Props) {
  const cols = offsets.filter((o) => o <= maxOffset);
  return (
    <div className="overflow-x-auto">
      <table className="border-separate border-spacing-[3px] text-[11px]">
        <thead>
          <tr>
            <th className="sticky left-0 bg-surface px-2 text-left font-medium text-muted">
              Cohort
            </th>
            {cols.map((o) => (
              <th key={o} className="w-9 min-w-9 text-center font-medium text-muted">
                {o}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {cohorts.map((c) => {
            const byOffset = new Map(c.points.map((p) => [p.offset, p.rate]));
            return (
              <tr key={c.cohort_month}>
                <td className="sticky left-0 bg-surface px-2 py-1 text-left tnum text-muted">
                  {c.cohort_month}
                </td>
                {cols.map((o) => {
                  const rate = byOffset.get(o);
                  if (rate === undefined) {
                    return <td key={o} className="h-7 w-9 rounded bg-canvas" />;
                  }
                  return (
                    <td
                      key={o}
                      className="h-7 w-9 rounded text-center tnum"
                      style={{ background: cellColor(rate), color: textColor(rate) }}
                      title={`${c.cohort_month} · month ${o} · ${(rate * 100).toFixed(0)}% retained (cohort ${c.size})`}
                    >
                      {o === 0 ? "" : Math.round(rate * 100)}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="mt-2 text-[11.5px] text-muted">
        Share of each monthly cohort active in later months. Column 0 is the acquisition month.
      </p>
    </div>
  );
}
