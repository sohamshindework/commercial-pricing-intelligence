import type { ApiError } from "../api/client";
import { useClv, useCohorts, useSegments } from "../api/hooks";
import { CHART } from "../charts/chartTheme";
import { CohortHeatmap } from "../charts/CohortHeatmap";
import { RankedBars } from "../charts/RankedBars";
import { TrendLine } from "../charts/TrendLine";
import { Card, ChartCard } from "../components/Card";
import { PageHeader } from "../components/PageHeader";
import { CompactStat } from "../components/Stat";
import { BarsSkeleton, ChartSkeleton } from "../components/Skeleton";
import { ErrorState } from "../components/states";
import { count, money, money2, moneyAxis, moneyCompact, percent } from "../lib/format";

export function Customers() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Customer Analytics"
        lede="Purchasing behaviour, retention and customer value for identified customers."
      />
      <Card className="border-l-[3px] border-l-sage p-4">
        <p className="text-[13px] leading-relaxed text-body">
          These are customer-model outputs over the full transaction history. Transactions
          without a customer identifier (about a fifth of revenue) are excluded, and the global
          date and market filters do not apply to this page.
        </p>
      </Card>

      <Segments />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <Cohorts />
        </div>
        <div className="lg:col-span-2">
          <RetentionCurve />
        </div>
      </div>
      <Clv />
    </div>
  );
}

function Segments() {
  const q = useSegments();
  return (
    <ChartCard title="Customer segments (RFM)" subtitle="Value and size by segment">
      {q.isLoading && <BarsSkeleton rows={8} />}
      {q.isError && <ErrorState message={(q.error as ApiError).message} />}
      {q.data && (
        <RankedBars
          data={q.data.items.map((s) => ({
            label: s.segment,
            value: s.monetary,
            meta: `${count(s.customers)} customers`,
          }))}
          height={Math.max(240, q.data.items.length * 30)}
          color={CHART.iris}
          valueFormat={money2}
          axisFormat={moneyAxis}
          labelWidth={176}
        />
      )}
    </ChartCard>
  );
}

function Cohorts() {
  const q = useCohorts();
  return (
    <ChartCard title="Cohort retention" subtitle="Monthly cohorts by first purchase">
      {q.isLoading && <ChartSkeleton height={320} />}
      {q.isError && <ErrorState message={(q.error as ApiError).message} />}
      {q.data && <CohortHeatmap offsets={q.data.offsets} cohorts={q.data.cohorts} />}
    </ChartCard>
  );
}

function RetentionCurve() {
  const q = useCohorts();
  return (
    <ChartCard title="Average retention" subtitle="By months since first purchase">
      {q.isLoading && <ChartSkeleton height={260} />}
      {q.isError && <ErrorState message={(q.error as ApiError).message} />}
      {q.data && (
        <TrendLine
          data={q.data.curve.map((c) => ({ label: `M${c.offset}`, value: c.retention }))}
          height={260}
          valueFormat={(v) => percent(v * 100)}
          axisFormat={(v) => percent(v * 100, 0)}
          labelText={(l) => `Month ${l.slice(1)}`}
        />
      )}
    </ChartCard>
  );
}

function Clv() {
  const q = useClv();
  return (
    <ChartCard
      title="Customer value (180-day repeat horizon)"
      subtitle={q.data?.period_note ?? "Out-of-sample evaluation"}
    >
      {q.isLoading && <BarsSkeleton rows={6} />}
      {q.isError && <ErrorState message={(q.error as ApiError).message} />}
      {q.data && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-border text-left text-muted">
                  <th className="py-2 font-medium">Model</th>
                  <th className="py-2 text-right font-medium">MAE (GBP)</th>
                  <th className="py-2 text-right font-medium">RMSE (GBP)</th>
                </tr>
              </thead>
              <tbody>
                {q.data.metrics.map((m) => (
                  <tr key={m.method} className="border-b border-border last:border-0">
                    <td className="py-2 text-body">{m.method}</td>
                    <td className="py-2 text-right tnum text-ink">{money2(m.mae)}</td>
                    <td className="py-2 text-right tnum text-ink">{money2(m.rmse)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-3">
              <CompactStat label="Chosen model" value={q.data.winner} />
              <CompactStat label="Average predicted value" value={money2(q.data.avg_clv)} />
              <CompactStat label="Total predicted value" value={moneyCompact(q.data.total_clv)} />
            </div>
            <p className="mt-3 text-[12px] leading-relaxed text-muted">
              The chosen approach has the lower held-out customer-value error in GBP. The same
              approach drives every score and chart; values are non-negative, undiscounted ranking
              aids rather than guaranteed forecasts.
            </p>
          </div>
          <div className="lg:col-span-3">
            <p className="mb-2 text-[12.5px] text-muted">Predicted-value distribution</p>
            <RankedBars
              data={q.data.distribution.map((b) => ({
                label: `${money(b.lower)}–${money(b.upper)}`,
                value: b.count,
              }))}
              height={300}
              color={CHART.lilac}
              valueFormat={(v) => `${count(v)} customers`}
              axisFormat={(v) => count(v)}
              labelWidth={130}
            />
          </div>
        </div>
      )}
    </ChartCard>
  );
}
