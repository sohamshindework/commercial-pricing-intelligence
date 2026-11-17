import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Executive } from "../pages/Executive";

const state = vi.hoisted(() => ({ fail: false }));

const ready = (data: unknown) => ({ data, isLoading: false, isError: false, error: null });
const failed = { data: undefined, isLoading: false, isError: true, error: new Error("Evidence service failed") };

vi.mock("../api/hooks", () => ({
  useExecutive: () =>
    state.fail
      ? failed
      : ready({
          situation: "Revenue is resilient while cancellation impact remains visible.",
          headline: {
            net_revenue: 17100655.84,
            sale_invoices: 39516,
            cancellation_invoices: 7406,
            gross_sales_aov: 450.2,
            active_customers: 5800,
            yoy_pct: 4.2,
            yoy_label: "Comparable period YoY",
          },
          recommendations: [
            {
              priority: 1,
              action: "Pilot a price floor",
              evidence: "Observed dispersion",
              scenario_impact: "Hypothetical only",
              success_metric: "Incremental net revenue",
              confidence: "Medium — requires randomised validation",
            },
          ],
          monitoring_kpis: [{ name: "Net revenue", definition: "Gross sales less cancellations." }],
          limitations: ["Observational history is not a causal estimate."],
        }),
  useRevenueBridge: () =>
    ready({
      comparison_label: "2011 vs 2010 comparable period",
      components: [{ component: "Mix", value_gbp: 125000, kind: "delta" }],
    }),
  useSegments: () =>
    ready({
      items: [
        { segment: "Champions", customers: 100, monetary: 500000 },
        { segment: "Loyal", customers: 150, monetary: 300000 },
        { segment: "Potential", customers: 200, monetary: 200000 },
      ],
    }),
  useClv: () => ready({ winner: "historical_mean", avg_clv: 312.5 }),
  useOpportunities: () =>
    ready({
      items: [
        { name: "Price consistency", impact_low_gbp: 10000, impact_high_gbp: 25000 },
      ],
    }),
  useExperimentSummary: () =>
    ready({
      eligible_products: 3427,
      available_products_per_arm: 1713,
      required_products_per_arm: 21102,
      mde_available_relative: 0.176,
    }),
}));

describe("Executive Decisions", () => {
  beforeEach(() => {
    state.fail = false;
  });

  it("connects metrics, recommendations and the experiment gate", () => {
    render(
      <MemoryRouter>
        <Executive />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Executive Decisions" })).toBeInTheDocument();
    expect(screen.getByText("39,516")).toBeInTheDocument();
    expect(screen.getByText(/5% test is not adequately powered/i)).toBeInTheDocument();
    expect(screen.getAllByText("17.6%").length).toBeGreaterThan(0);
    expect(screen.getByText(/Pricing manager \+ category lead \(suggested\)/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Review assumptions and power curve/ })).toHaveAttribute(
      "href",
      "/pricing",
    );
  });

  it("renders an actionable failure state", () => {
    state.fail = true;
    render(
      <MemoryRouter>
        <Executive />
      </MemoryRouter>,
    );
    expect(screen.getByText("Evidence service failed")).toBeInTheDocument();
  });
});
