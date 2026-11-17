import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../api/client";
import { resetStaticSnapshotForTests, staticGet } from "../api/staticData";

const response = (label: string) => ({ label });
const snapshot = {
  metadata: response("metadata"),
  filtered: {
    "market=*&family=*": {
      overview: response("overview-all"),
      revenue_trend: response("trend-all"),
      revenue_by_family: response("family-all"),
      revenue_by_market: response("market-all"),
      products: { filters: {}, items: [{ id: 1 }, { id: 2 }, { id: 3 }], total: 3 },
    },
    "market=UK&family=KD": {
      overview: response("overview-filtered"),
      revenue_trend: response("trend-filtered"),
      revenue_by_family: response("family-filtered"),
      revenue_by_market: response("market-filtered"),
      products: { filters: {}, items: [{ id: 9 }], total: 1 },
    },
  },
  fixed: {
    bridge_product: response("bridge"),
    bridge_customer: response("bridge-customer"),
    bridge_geography: response("bridge-geography"),
    classification: response("classification"),
    segments: response("segments"),
    cohorts: response("cohorts"),
    clv: response("clv"),
    dispersion: response("dispersion"),
    price_response: response("price-response"),
    experiment_summary: response("experiment"),
    power_curve: response("power"),
    executive: response("executive"),
  },
  opportunities: { "0.20:0.50": response("opportunity") },
};

beforeEach(() => {
  resetStaticSnapshotForTests();
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify(snapshot), { status: 200, headers: { "Content-Type": "application/json" } }),
    ),
  );
});

describe("verified static data resolver", () => {
  it("loads every five-route data dependency without calling a backend", async () => {
    const paths = [
      "/api/metadata",
      "/api/overview",
      "/api/revenue/trend",
      "/api/revenue/bridge?lens=product",
      "/api/revenue/by-family",
      "/api/revenue/by-market",
      "/api/products/top?limit=2&offset=0",
      "/api/products/classification",
      "/api/customers/segments",
      "/api/customers/cohorts",
      "/api/customers/clv",
      "/api/pricing/opportunities?capture_low=0.2&capture_high=0.5",
      "/api/pricing/dispersion?limit=15",
      "/api/pricing/price-response",
      "/api/experiments/summary",
      "/api/experiments/power-curve",
      "/api/executive/summary",
    ];
    for (const path of paths) expect(await staticGet(path)).toBeDefined();
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(vi.mocked(fetch).mock.calls[0][0]).toBe("/data/portfolio-demo.json");
  });

  it("applies exact market and family selections and paginates locally", async () => {
    expect(
      await staticGet("/api/overview?market=UK&family=KD"),
    ).toEqual(response("overview-filtered"));
    const page = await staticGet<{ items: unknown[]; total: number; offset: number }>(
      "/api/products/top?limit=1&offset=1",
    );
    expect(page.items).toEqual([{ id: 2 }]);
    expect(page.total).toBe(3);
    expect(page.offset).toBe(1);
  });

  it("rejects unsupported dates, invalid filters and off-grid pricing inputs", async () => {
    await expect(staticGet("/api/overview?start=2011-01-01")).rejects.toBeInstanceOf(ApiError);
    await expect(staticGet("/api/overview?market=Mars")).rejects.toBeInstanceOf(ApiError);
    await expect(
      staticGet("/api/pricing/opportunities?capture_low=0.21&capture_high=0.5"),
    ).rejects.toBeInstanceOf(ApiError);
    await expect(
      staticGet("/api/pricing/opportunities?capture_low=0.6&capture_high=0.3"),
    ).rejects.toBeInstanceOf(ApiError);
  });
});
