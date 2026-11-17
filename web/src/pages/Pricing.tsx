import { useState } from "react";

import type { ApiError } from "../api/client";
import {
  useDispersion,
  useExperimentSummary,
  useOpportunities,
  usePowerCurve,
  usePriceResponse,
} from "../api/hooks";
import type { DispersionProduct } from "../api/types";
import { CHART } from "../charts/chartTheme";
import { RankedBars } from "../charts/RankedBars";
import { TrendLine } from "../charts/TrendLine";
import { Card, ChartCard } from "../components/Card";
import { type Column, DataTable } from "../components/DataTable";
import { PageHeader } from "../components/PageHeader";
import { RangeInput } from "../components/RangeInput";
import { BarsSkeleton, ChartSkeleton, TableSkeleton } from "../components/Skeleton";
import { ErrorState } from "../components/states";
import { count, money, money2, percent } from "../lib/format";

export function Pricing() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Pricing & Experiments"
        lede="Commercial opportunities and whether proposed changes are worth testing."
      />
      <Card className="border-l-[3px] border-l-warning p-4">
        <p className="text-[13px] leading-relaxed text-body">
          Observed patterns and hypothetical scenarios are kept separate. Nothing here is a
          causal price effect or a profit figure: there is no cost data, revenue ranges are
          scenarios under a stated assumption, and a price change is validated only by the
          experiment below.
        </p>
      </Card>

      <Opportunities />
      <PriceResponse />
      <Dispersion />
      <Experiment />
    </div>
  );
}

function Opportunities() {
  const [low, setLow] = useState(0.2);
  const [high, setHigh] = useState(0.5);
  const q = useOpportunities(low, high);

  return (
    <Card className="p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="font-heading text-[17px] text-ink">Revenue opportunities</h3>
          <p className="mt-0.5 text-[12.5px] text-muted">
            Scenario range = measured gap × the recoverable share you assume.
          </p>
        </div>
        <div className="grid w-full max-w-xs grid-cols-2 gap-4">
          <RangeInput label="Low capture" value={low} max={high} onChange={setLow} />
          <RangeInput label="High capture" value={high} min={low} onChange={setHigh} />
        </div>
      </div>
      {q.isLoading && !q.data && <BarsSkeleton rows={2} />}
      {q.isError && <ErrorState message={(q.error as ApiError).message} />}
      {q.data && (
        <div className="space-y-3">
          {q.data.items.map((o) => (
            <div key={o.key} className="rounded-lg border border-border p-4">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="font-heading text-[14.5px] text-ink">{o.name}</span>
                <span className="font-heading text-[16px] tnum text-iris">
                  {money(o.impact_low_gbp)} – {money(o.impact_high_gbp)}
                </span>
              </div>
              <div className="mt-1 flex flex-wrap gap-x-5 gap-y-1 text-[12.5px] text-muted">
                <span>Measured gap {money(o.measured_gap_gbp)}</span>
                <span>
                  {percent(o.impact_low_pct_rev, 1)}–{percent(o.impact_high_pct_rev, 1)} of net
                  revenue
                </span>
                <span>
                  Margin scenario {money(o.margin_low_gbp)} – {money(o.margin_high_gbp)}
                </span>
              </div>
            </div>
          ))}
          <p className="text-[12px] text-muted">
            Margin uses an assumed cost ratio of {percent(q.data.assumed_cost_ratio * 100, 0)} — a
            labelled scenario, not a measured margin.
          </p>
        </div>
      )}
    </Card>
  );
}

function PriceResponse() {
  const q = usePriceResponse();
  return (
    <ChartCard
      title="Price–quantity association by family"
      subtitle="Within-product, descriptive — not a price elasticity"
    >
      {q.isLoading && <BarsSkeleton rows={8} />}
      {q.isError && <ErrorState message={(q.error as ApiError).message} />}
      {q.data && (
        <>
          <RankedBars
            data={[...q.data.items]
              .sort((a, b) => a.within_slope - b.within_slope)
              .map((r) => ({
                label: r.name,
                value: r.within_slope,
                meta: `95% CI ${r.within_ci_low.toFixed(2)} to ${r.within_ci_high.toFixed(2)} · ${count(r.n_lines)} lines`,
              }))}
            height={Math.max(240, q.data.items.length * 26)}
            color={CHART.iris}
            valueFormat={(v) => v.toFixed(2)}
            axisFormat={(v) => v.toFixed(1)}
            labelWidth={176}
          />
          <p className="mt-2 text-[12px] text-muted">{q.data.note}</p>
        </>
      )}
    </ChartCard>
  );
}

function Dispersion() {
  const q = useDispersion();
  const columns: Column<DispersionProduct>[] = [
    { key: "name", header: "Product", align: "left", render: (r) => r.product_name },
    { key: "min", header: "Min", align: "right", render: (r) => money2(r.price_min) },
    { key: "med", header: "Median", align: "right", render: (r) => money2(r.price_median) },
    { key: "max", header: "Max", align: "right", render: (r) => money2(r.price_max) },
    { key: "cv", header: "Variation", align: "right", render: (r) => r.price_cv.toFixed(2) },
  ];
  return (
    <Card className="p-5">
      <h3 className="font-heading text-[17px] text-ink">Price dispersion</h3>
      <p className="mb-3 mt-0.5 text-[12.5px] text-muted">
        Best-selling products sold across a wide range of unit prices.
      </p>
      {q.isLoading && <TableSkeleton rows={8} />}
      {q.isError && <ErrorState message={(q.error as ApiError).message} />}
      {q.data && (
        <DataTable columns={columns} rows={q.data.items} rowKey={(r) => r.product_key} />
      )}
    </Card>
  );
}

function Experiment() {
  const summary = useExperimentSummary();
  const curve = usePowerCurve();
  return (
    <ChartCard
      title="Experiment sizing"
      subtitle="SKU-randomised price-floor test · repeated weeks aggregated per SKU"
    >
      {(summary.isLoading || curve.isLoading) && <ChartSkeleton height={280} />}
      {summary.isError && <ErrorState message={(summary.error as ApiError).message} />}
      {summary.data && curve.data && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
          <div className="lg:col-span-2 space-y-3">
            <Stat
              label="Detectable effect with available SKUs"
              value={percent(summary.data.mde_available_relative * 100, 1)}
            />
            <Stat
              label="Available SKUs per arm"
              value={count(summary.data.available_products_per_arm)}
            />
            <Stat
              label="SKUs per arm needed for 5%"
              value={count(summary.data.required_products_per_arm)}
            />
            <Stat label="Duration" value={`${summary.data.duration_weeks} weeks`} />
            <Stat
              label="Power / significance"
              value={`${percent(summary.data.power * 100, 0)} · α ${summary.data.alpha}`}
            />
            <p className="text-[12px] leading-relaxed text-muted">
              The 5% target is not adequately powered. The adjusted estimate assumes the
              historical pre-period correlation persists; a smaller pilot can validate
              operations, but not efficacy.
            </p>
          </div>
          <div className="lg:col-span-3">
            <p className="mb-2 text-[12.5px] text-muted">
              Adjusted minimum detectable effect vs independent SKUs per arm
            </p>
            <TrendLine
              data={curve.data.points.map((p) => ({
                label: p.n_per_group >= 1000 ? `${p.n_per_group / 1000}k` : `${p.n_per_group}`,
                value: p.mde_relative * 100,
              }))}
              height={260}
              valueFormat={(v) => percent(v, 1)}
              axisFormat={(v) => percent(v, 0)}
              labelText={(l) => `${l} SKUs per arm`}
            />
          </div>
        </div>
      )}
    </ChartCard>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between border-b border-border pb-2.5 last:border-0">
      <span className="text-[13px] text-body">{label}</span>
      <span className="font-heading text-[16px] tnum text-ink">{value}</span>
    </div>
  );
}
