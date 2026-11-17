import { useEffect, useMemo, useState } from "react";

import type { ApiError } from "../api/client";
import {
  useClassification,
  useMetadata,
  useRevenueBridge,
  useRevenueByFamily,
  useRevenueByMarket,
  useTopProducts,
} from "../api/hooks";
import type { Product } from "../api/types";
import { CHART } from "../charts/chartTheme";
import { RankedBars } from "../charts/RankedBars";
import { Waterfall } from "../charts/Waterfall";
import { Card, ChartCard } from "../components/Card";
import { type Column, DataTable, Pagination } from "../components/DataTable";
import { FilterBar } from "../components/FilterBar";
import { PageHeader } from "../components/PageHeader";
import { Segmented } from "../components/Segmented";
import { BarsSkeleton, ChartSkeleton, TableSkeleton } from "../components/Skeleton";
import { EmptyState, ErrorState } from "../components/states";
import { count, money, money2, moneyAxis, moneyCompact, percent } from "../lib/format";
import { useFilters } from "../state/filters";

type Filters = ReturnType<typeof useFilters>["filters"];
type NameFn = (code: string) => string;
const PAGE = 10;

export function RevenueProduct() {
  const { filters } = useFilters();
  const { data: meta } = useMetadata();
  const familyName = useMemo<NameFn>(() => {
    const m = new Map(meta?.families.map((f) => [f.family_code, f.name]));
    return (code) => m.get(code) ?? (code === "NA" ? "Unclassified" : code);
  }, [meta]);
  const selectedFamily = filters.family ? familyName(filters.family) : null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Revenue & Products"
        lede="Where revenue comes from and why it changes — price, volume and mix, category contribution, and the products that drive performance."
      />
      <FilterBar />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <RevenueDrivers />
        </div>
        <div className="lg:col-span-2">
          <MarketMix filters={filters} />
        </div>
      </div>

      <CategoryContribution filters={filters} familyName={familyName} selectedFamily={selectedFamily} />
      <ProductRankings filters={filters} familyName={familyName} />
      <Classification familyName={familyName} />
    </div>
  );
}

type Lens = "product" | "customer" | "geography";
const LENS_NOTE: Record<Lens, string> = {
  product:
    "Price, volume and mix are a descriptive attribution of the revenue change, not a causal price effect.",
  customer: "New, lost and retained-customer contributions to the revenue change.",
  geography: "Contribution to the revenue change by market.",
};

function RevenueDrivers() {
  const [lens, setLens] = useState<Lens>("product");
  const bridge = useRevenueBridge(lens);
  return (
    <ChartCard
      title="Revenue drivers"
      subtitle={bridge.data ? `Comparison: ${bridge.data.comparison_label}` : "Comparison period"}
      action={
        <Segmented
          ariaLabel="Decomposition lens"
          value={lens}
          onChange={setLens}
          options={[
            { value: "product", label: "Product" },
            { value: "customer", label: "Customer" },
            { value: "geography", label: "Geography" },
          ]}
        />
      }
    >
      {bridge.isLoading && <ChartSkeleton height={320} />}
      {bridge.isError && <ErrorState message={(bridge.error as ApiError).message} />}
      {bridge.data && (
        <>
          <Waterfall
            steps={bridge.data.components.map((c) => ({
              label: c.component,
              value: c.value_gbp,
              kind: c.kind,
            }))}
            height={320}
            valueFormat={moneyCompact}
          />
          <p className="mt-2 text-[12px] text-muted">{LENS_NOTE[lens]}</p>
        </>
      )}
    </ChartCard>
  );
}

function MarketMix({ filters }: { filters: Filters }) {
  const q = useRevenueByMarket(filters);
  const items = q.data?.items ?? [];
  const total = items.reduce((s, m) => s + m.net_revenue, 0);
  const share = (v: number) => (total ? (v / total) * 100 : 0);
  return (
    <ChartCard title="Revenue by market">
      {q.isLoading && <BarsSkeleton rows={3} />}
      {q.isError && <ErrorState message={(q.error as ApiError).message} />}
      {q.data && items.length === 0 && <EmptyState title="No revenue in this selection" />}
      {q.data && items.length > 0 && (
        <>
          <RankedBars
            data={items.map((m) => ({
              label: m.market,
              value: m.net_revenue,
              meta: `${percent(share(m.net_revenue))} of selection`,
            }))}
            height={Math.max(150, items.length * 48)}
            color={CHART.sage}
            valueFormat={money2}
            axisFormat={moneyAxis}
            labelWidth={96}
          />
          <p className="mt-1 text-[12px] text-muted">
            {items.map((m) => `${m.market} ${percent(share(m.net_revenue), 0)}`).join(" · ")}
          </p>
        </>
      )}
    </ChartCard>
  );
}

function CategoryContribution({
  filters,
  familyName,
  selectedFamily,
}: {
  filters: Filters;
  familyName: NameFn;
  selectedFamily: string | null;
}) {
  const q = useRevenueByFamily(filters);
  const items = q.data?.items ?? [];
  const total = items.reduce((s, f) => s + f.net_revenue, 0);

  if (selectedFamily) {
    return (
      <ChartCard title="Category contribution" subtitle="Net revenue by product family">
        <EmptyState
          title={`Filtered to ${selectedFamily}`}
          detail="Clear the product-family filter to compare families."
        />
      </ChartCard>
    );
  }
  return (
    <ChartCard title="Category contribution" subtitle="Net revenue by product family">
      {q.isLoading && <BarsSkeleton rows={8} />}
      {q.isError && <ErrorState message={(q.error as ApiError).message} />}
      {q.data && items.length === 0 && <EmptyState title="No revenue in this selection" />}
      {q.data && items.length > 0 && (
        <RankedBars
          data={items.map((f) => ({
            label: familyName(f.family_code),
            value: f.net_revenue,
            meta: total ? `${percent((f.net_revenue / total) * 100)} of selection` : undefined,
          }))}
          height={Math.max(220, items.length * 26)}
          color={CHART.iris}
          valueFormat={money2}
          axisFormat={moneyAxis}
          labelWidth={168}
        />
      )}
    </ChartCard>
  );
}

function ProductRankings({ filters, familyName }: { filters: Filters; familyName: NameFn }) {
  const [offset, setOffset] = useState(0);
  const q = useTopProducts(filters, PAGE, offset);

  useEffect(() => setOffset(0), [filters.start, filters.end, filters.market, filters.family]);

  const columns: Column<Product>[] = [
    { key: "name", header: "Product", align: "left", render: (r) => r.product_name },
    { key: "family", header: "Family", align: "left", render: (r) => familyName(r.family_code) },
    { key: "rev", header: "Net revenue", align: "right", render: (r) => money(r.net_revenue) },
    { key: "units", header: "Units", align: "right", render: (r) => count(r.units) },
  ];

  return (
    <Card className="p-5">
      <h3 className="mb-3 font-heading text-[17px] text-ink">Product performance</h3>
      {q.isLoading && !q.data && <TableSkeleton rows={PAGE} />}
      {q.isError && <ErrorState message={(q.error as ApiError).message} />}
      {q.data && q.data.items.length === 0 && <EmptyState title="No products in this selection" />}
      {q.data && q.data.items.length > 0 && (
        <>
          <DataTable columns={columns} rows={q.data.items} rowKey={(r) => r.product_key} />
          <Pagination offset={offset} limit={PAGE} total={q.data.total} onPage={setOffset} />
        </>
      )}
    </Card>
  );
}

function Classification({ familyName }: { familyName: NameFn }) {
  const q = useClassification();
  return (
    <ChartCard
      title="Product classification quality"
      subtitle={q.data?.period_note ?? "Held-out test set"}
    >
      {q.isLoading && <BarsSkeleton rows={8} />}
      {q.isError && <ErrorState message={(q.error as ApiError).message} />}
      {q.data && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-border text-left text-muted">
                  <th className="py-2 font-medium">Method</th>
                  <th className="py-2 text-right font-medium">Accuracy</th>
                  <th className="py-2 text-right font-medium">Macro-F1</th>
                </tr>
              </thead>
              <tbody>
                {q.data.metrics.map((m) => (
                  <tr key={m.method} className="border-b border-border last:border-0">
                    <td className="py-2 text-body">{m.method}</td>
                    <td className="py-2 text-right tnum text-ink">{percent(m.accuracy * 100)}</td>
                    <td className="py-2 text-right tnum text-ink">{m.macro_f1.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-3 text-[12px] leading-relaxed text-muted">
              TF-IDF with logistic regression is the selected, independently evaluated method.
              The former language-model comparison was withdrawn because its replay labels were
              not independent of the gold set. Classes with few test examples have noisier F1.
            </p>
          </div>
          <div className="lg:col-span-3">
            <RankedBars
              data={[...q.data.per_class]
                .sort((a, b) => b.f1 - a.f1)
                .map((r) => ({
                  label: familyName(r.family_code),
                  value: r.f1,
                  meta: `support: ${r.support} test items`,
                }))}
              height={Math.max(220, q.data.per_class.length * 24)}
              color={CHART.lilac}
              valueFormat={(v) => v.toFixed(3)}
              axisFormat={(v) => v.toFixed(1)}
              labelWidth={168}
            />
          </div>
        </div>
      )}
    </ChartCard>
  );
}
