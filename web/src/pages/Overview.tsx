import { Link } from "react-router-dom";

import type { ApiError } from "../api/client";
import { useOverview, useRevenueBridge, useRevenueTrend } from "../api/hooks";
import type { RevenueBridgeResponse } from "../api/types";
import { CHART } from "../charts/chartTheme";
import { TrendLine } from "../charts/TrendLine";
import { Waterfall } from "../charts/Waterfall";
import { Card, ChartCard } from "../components/Card";
import { FilterBar } from "../components/FilterBar";
import { PageHeader } from "../components/PageHeader";
import { ChartSkeleton } from "../components/Skeleton";
import { CompactStat, PrimaryStat, SupportingStat } from "../components/Stat";
import { EmptyState, ErrorState, Loading } from "../components/states";
import {
  count,
  money,
  money2,
  moneyAxis,
  moneyCompact,
  percent,
  signedPercent,
} from "../lib/format";
import { useFilters } from "../state/filters";

export function Overview() {
  const { filters } = useFilters();
  const overview = useOverview(filters);
  const trend = useRevenueTrend(filters);
  const bridge = useRevenueBridge("product");

  return (
    <div className="space-y-6">
      <PageHeader
        title="Commercial Performance"
        lede="Revenue, customers and product performance in one decision workspace."
      />
      <FilterBar />

      {bridge.data && <PerformanceSummary data={bridge.data} />}

      {overview.isLoading && <Loading />}
      {overview.isError && <ErrorState message={(overview.error as ApiError).message} />}
      {overview.data && (
        <Card className="grid grid-cols-1 divide-border p-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)_minmax(0,1fr)] lg:divide-x">
          <div className="pb-4 lg:pb-0 lg:pr-6">
            <PrimaryStat label="Net revenue" value={moneyCompact(overview.data.kpis.net_revenue)} />
          </div>
          <div className="border-t border-border py-4 lg:border-0 lg:px-6 lg:py-0">
            <SupportingStat
              label="Sale invoices"
              value={count(overview.data.kpis.sale_invoices)}
            />
          </div>
          <div className="border-t border-border pt-4 lg:border-0 lg:pl-6 lg:pt-0">
            <SupportingStat
              label="Gross sales AOV"
              value={money2(overview.data.kpis.gross_sales_aov)}
            />
          </div>
        </Card>
      )}

      <ChartCard title="Monthly revenue">
        {trend.isLoading && <ChartSkeleton height={330} />}
        {trend.isError && <ErrorState message={(trend.error as ApiError).message} />}
        {trend.data && trend.data.points.length === 0 && (
          <EmptyState title="No revenue in this selection" detail="Try widening the filters." />
        )}
        {trend.data && trend.data.points.length > 0 && (
          <TrendLine
            data={trend.data.points.map((p) => ({ label: p.year_month, value: p.net_revenue }))}
            height={330}
            valueFormat={money2}
            axisFormat={moneyAxis}
            labelText={(l) => `Month ${l}`}
          />
        )}
      </ChartCard>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <ChartCard
            title="Revenue drivers"
            subtitle={
              bridge.data ? `Comparison: ${bridge.data.comparison_label}` : "Comparison period"
            }
          >
            {bridge.isLoading && <ChartSkeleton height={300} />}
            {bridge.isError && <ErrorState message={(bridge.error as ApiError).message} />}
            {bridge.data && (
              <Waterfall
                steps={bridge.data.components.map((c) => ({
                  label: c.component,
                  value: c.value_gbp,
                  kind: c.kind,
                }))}
                height={300}
                valueFormat={moneyCompact}
              />
            )}
          </ChartCard>
        </div>
        <div className="lg:col-span-2">
          <CommercialFindings data={bridge.data} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <div className="lg:col-span-2">
          {overview.data && (
            <Card className="p-5">
              <h3 className="mb-2 font-heading text-[16px] text-ink">Customer coverage</h3>
              <CompactStat
                label="Active customers"
                value={count(overview.data.kpis.active_customers)}
              />
              <CompactStat label="Units sold" value={count(overview.data.kpis.units_sold)} />
              <CompactStat
                label="Cancellation invoices"
                value={count(overview.data.kpis.cancellation_invoices)}
                hint={money(overview.data.kpis.cancellations)}
              />
              <CompactStat
                label="Unidentified-customer revenue"
                value={percent(overview.data.kpis.guest_revenue_pct)}
                hint="no customer id"
              />
            </Card>
          )}
        </div>
        <div className="lg:col-span-3">
          <ContinueTo />
        </div>
      </div>

    </div>
  );
}

function bridgeYoY(data: RevenueBridgeResponse) {
  const start = data.components.find((c) => c.kind === "start")?.value_gbp ?? 0;
  const end = data.components.find((c) => c.kind === "end")?.value_gbp ?? 0;
  return { start, end, pct: start ? ((end - start) / start) * 100 : 0 };
}

function topDrivers(data: RevenueBridgeResponse) {
  return [...data.components.filter((c) => c.kind === "delta")].sort(
    (a, b) => Math.abs(b.value_gbp) - Math.abs(a.value_gbp),
  );
}

function PerformanceSummary({ data }: { data: RevenueBridgeResponse }) {
  const { pct } = bridgeYoY(data);
  const drivers = topDrivers(data);
  const up = drivers.find((d) => d.value_gbp > 0);
  const down = drivers.find((d) => d.value_gbp < 0);
  return (
    <Card className="border-l-[3px] border-l-coral p-5">
      <p className="text-[12.5px] font-semibold uppercase tracking-wide text-coral">
        Performance summary
      </p>
      <p className="mt-2 max-w-3xl text-[15px] leading-relaxed text-body">
        Over the comparison period ({data.comparison_label}), net revenue changed{" "}
        <strong className="tnum text-ink">{signedPercent(pct)}</strong>
        {up && (
          <>
            , supported by {up.component.toLowerCase()} of{" "}
            <strong className="tnum text-ink">{money(up.value_gbp)}</strong>
          </>
        )}
        {down && (
          <>
            , while {down.component.toLowerCase()} reduced revenue by{" "}
            <strong className="tnum text-ink">{money(Math.abs(down.value_gbp))}</strong>
          </>
        )}
        . These are descriptive attributions, not causal price effects.
      </p>
    </Card>
  );
}

function CommercialFindings({ data }: { data: RevenueBridgeResponse | undefined }) {
  return (
    <Card className="h-full p-5">
      <h3 className="font-heading text-[16px] text-ink">Commercial findings</h3>
      <p className="mt-0.5 text-[12.5px] text-muted">Ranked revenue drivers for the comparison.</p>
      <ul className="mt-3 space-y-2.5">
        {data &&
          topDrivers(data)
            .slice(0, 6)
            .map((d) => {
              const positive = d.value_gbp >= 0;
              return (
                <li key={d.component} className="flex items-center gap-3">
                  <span
                    className="h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ background: positive ? CHART.positive : CHART.negative }}
                  />
                  <span className="flex-1 text-[13.5px] text-body">{d.component}</span>
                  <span
                    className="font-heading text-[13.5px] tnum"
                    style={{ color: positive ? CHART.positive : CHART.negative }}
                  >
                    {signedPercent((d.value_gbp / Math.abs(bridgeYoY(data).start)) * 100, 1)}
                  </span>
                  <span className="w-20 text-right text-[13px] tnum text-muted">
                    {moneyCompact(d.value_gbp)}
                  </span>
                </li>
              );
            })}
      </ul>
    </Card>
  );
}

const DEEPER = [
  { to: "/revenue", label: "Revenue & Products", note: "Price, volume and mix, by category" },
  { to: "/customers", label: "Customer Analytics", note: "Segments, retention and value" },
  { to: "/pricing", label: "Pricing & Experiments", note: "Opportunities and test design" },
  { to: "/executive", label: "Executive Decisions", note: "Evidence, priorities and next steps" },
];

function ContinueTo() {
  return (
    <Card className="h-full p-5">
      <h3 className="font-heading text-[16px] text-ink">Go deeper</h3>
      <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-4">
        {DEEPER.map((d) => (
          <Link
            key={d.to}
            to={d.to}
            className="group rounded-lg border border-border p-3 transition hover:border-iris hover:bg-surface-alt"
          >
            <p className="font-heading text-[14px] text-ink group-hover:text-iris">{d.label}</p>
            <p className="mt-1 text-[12px] text-muted">{d.note}</p>
          </Link>
        ))}
      </div>
    </Card>
  );
}
