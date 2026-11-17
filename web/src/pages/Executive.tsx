import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import type { ApiError } from "../api/client";
import {
  useClv,
  useExecutive,
  useExperimentSummary,
  useOpportunities,
  useRevenueBridge,
  useSegments,
} from "../api/hooks";
import { Card } from "../components/Card";
import { PageHeader } from "../components/PageHeader";
import { RecommendedActions } from "../components/Recommendations";
import { BarsSkeleton } from "../components/Skeleton";
import { ErrorState } from "../components/states";
import { count, money, percent } from "../lib/format";

export function Executive() {
  const executive = useExecutive();
  const bridge = useRevenueBridge("product");
  const segments = useSegments();
  const clv = useClv();
  const opportunities = useOpportunities(0.2, 0.5);
  const experiment = useExperimentSummary();

  const queries = [executive, bridge, segments, clv, opportunities, experiment];
  const error = queries.find((query) => query.isError)?.error as ApiError | undefined;

  if (error) return <ErrorState message={error.message} />;
  if (queries.some((query) => query.isLoading)) return <BarsSkeleton rows={7} />;
  if (
    !executive.data ||
    !bridge.data ||
    !segments.data ||
    !clv.data ||
    !opportunities.data ||
    !experiment.data
  ) {
    return <ErrorState message="Executive evidence is unavailable." />;
  }

  const headline = executive.data.headline;
  const topSegments = [...segments.data.items].sort((a, b) => b.monetary - a.monetary).slice(0, 3);
  const leadingOpportunity = [...opportunities.data.items].sort(
    (a, b) => b.impact_high_gbp - a.impact_high_gbp,
  )[0];
  const largestDriver = [...bridge.data.components]
    .filter((component) => component.kind === "delta")
    .sort((a, b) => Math.abs(b.value_gbp) - Math.abs(a.value_gbp))[0];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Executive Decisions"
        lede="A decision layer connecting commercial performance, customer evidence and test feasibility. Recommendations are proposals—not assigned commitments or causal claims."
      />

      <Card className="overflow-hidden border-l-[3px] border-l-iris p-5 sm:p-6">
        <p className="text-[11.5px] font-semibold uppercase tracking-[0.12em] text-iris">
          Current situation
        </p>
        <h2 className="mt-2 max-w-4xl font-heading text-[22px] leading-snug text-ink">
          {executive.data.situation}
        </h2>
        <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-5">
          <Metric label="Net revenue" value={money(headline.net_revenue)} />
          <Metric label="Sale invoices" value={count(headline.sale_invoices)} />
          <Metric label="Cancellation invoices" value={count(headline.cancellation_invoices)} />
          <Metric label="Gross sales AOV" value={money(headline.gross_sales_aov)} />
          <Metric label={headline.yoy_label} value={percent(headline.yoy_pct, 1)} />
        </div>
      </Card>

      <section aria-labelledby="evidence-heading">
        <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 id="evidence-heading" className="font-heading text-[20px] text-ink">
              Decision evidence
            </h2>
            <p className="text-[12.5px] text-muted">Observed history unless explicitly labelled as a scenario.</p>
          </div>
        </div>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <EvidenceCard title="Revenue" link="/revenue" linkLabel="Explore revenue">
            <Evidence label="Largest bridge component" value={largestDriver?.component ?? "Unavailable"} />
            <Evidence label="Contribution" value={money(largestDriver?.value_gbp ?? 0)} />
            <Evidence label="Comparison" value={bridge.data.comparison_label} />
          </EvidenceCard>
          <EvidenceCard title="Customers" link="/customers" linkLabel="Explore customers">
            <Evidence
              label="Top monetary segments"
              value={topSegments.map((segment) => segment.segment).join(", ")}
            />
            <Evidence label="Selected CLV model" value={clv.data.winner} />
            <Evidence label="Average predicted CLV" value={money(clv.data.avg_clv)} />
          </EvidenceCard>
          <EvidenceCard title="Pricing" link="/pricing" linkLabel="Explore pricing">
            <Evidence label="Leading scenario" value={leadingOpportunity?.name ?? "Unavailable"} />
            <Evidence
              label="Hypothetical revenue range"
              value={
                leadingOpportunity
                  ? `${money(leadingOpportunity.impact_low_gbp)}–${money(leadingOpportunity.impact_high_gbp)}`
                  : "Unavailable"
              }
            />
            <Evidence label="Evidence status" value="Observed gap; impact is a scenario" />
          </EvidenceCard>
        </div>
      </section>

      <Card className="p-5 sm:p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-2xl">
            <p className="text-[11.5px] font-semibold uppercase tracking-[0.12em] text-warning">
              Experiment gate
            </p>
            <h2 className="mt-1 font-heading text-[20px] text-ink">
              The proposed 5% test is not adequately powered
            </h2>
            <p className="mt-2 text-[13.5px] leading-relaxed text-body">
              Historical data supports {count(experiment.data.eligible_products)} eligible SKUs,
              or {count(experiment.data.available_products_per_arm)} per arm. A 5% target requires {" "}
              {count(experiment.data.required_products_per_arm)} independent SKUs per arm. At the
              available sample, the adjusted detectable effect is {" "}
              {percent(experiment.data.mde_available_relative * 100, 1)}. A smaller pilot may test
              operations, but must not claim efficacy.
            </p>
          </div>
          <dl className="grid min-w-0 grid-cols-2 gap-3 sm:min-w-[320px]">
            <Metric label="Eligible SKUs" value={count(experiment.data.eligible_products)} />
            <Metric label="Available / arm" value={count(experiment.data.available_products_per_arm)} />
            <Metric label="Needed / arm" value={count(experiment.data.required_products_per_arm)} />
            <Metric label="Available-sample MDE" value={percent(experiment.data.mde_available_relative * 100, 1)} />
          </dl>
        </div>
        <Link className="mt-4 inline-flex text-[13px] font-semibold text-iris hover:underline" to="/pricing">
          Review assumptions and power curve →
        </Link>
      </Card>

      <RecommendedActions />

      <Card className="p-5">
        <h2 className="font-heading text-[18px] text-ink">Monitoring definitions</h2>
        <dl className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
          {executive.data.monitoring_kpis.map((kpi) => (
            <div key={kpi.name} className="rounded-lg bg-canvas p-3">
              <dt className="text-[12px] font-semibold text-ink">{kpi.name}</dt>
              <dd className="mt-1 text-[12.5px] leading-relaxed text-body">{kpi.definition}</dd>
            </div>
          ))}
        </dl>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg bg-canvas p-3">
      <dt className="text-[11px] font-medium uppercase tracking-wide text-muted">{label}</dt>
      <dd className="mt-1 break-words font-heading text-[17px] tnum text-ink">{value}</dd>
    </div>
  );
}

function EvidenceCard({
  title,
  link,
  linkLabel,
  children,
}: {
  title: string;
  link: string;
  linkLabel: string;
  children: ReactNode;
}) {
  return (
    <Card className="flex min-w-0 flex-col p-5">
      <h3 className="font-heading text-[17px] text-ink">{title}</h3>
      <dl className="mt-3 flex-1 space-y-3">{children}</dl>
      <Link className="mt-4 text-[13px] font-semibold text-iris hover:underline" to={link}>
        {linkLabel} →
      </Link>
    </Card>
  );
}

function Evidence({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[11px] font-medium uppercase tracking-wide text-muted">{label}</dt>
      <dd className="mt-0.5 break-words text-[13px] text-body">{value}</dd>
    </div>
  );
}
