import { ApiError } from "./client";

interface StaticSnapshot {
  metadata: unknown;
  filtered: Record<
    string,
    {
      overview: unknown;
      revenue_trend: unknown;
      revenue_by_family: unknown;
      revenue_by_market: unknown;
      products: { filters: unknown; items: unknown[]; total: number };
    }
  >;
  fixed: Record<string, unknown>;
  opportunities: Record<string, unknown>;
}

let snapshotPromise: Promise<StaticSnapshot> | undefined;

function snapshotUrl(): string {
  return `${import.meta.env.BASE_URL}data/portfolio-demo.json`;
}

async function loadSnapshot(): Promise<StaticSnapshot> {
  if (!snapshotPromise) {
    snapshotPromise = fetch(snapshotUrl(), { headers: { Accept: "application/json" } }).then(
      async (response) => {
        if (!response.ok) {
          throw new ApiError(response.status, "The verified portfolio snapshot is unavailable.");
        }
        return (await response.json()) as StaticSnapshot;
      },
      () => {
        throw new ApiError(0, "The verified portfolio snapshot could not be loaded.");
      },
    );
  }
  return snapshotPromise;
}

function selectionKey(params: URLSearchParams): string {
  if (params.has("start") || params.has("end")) {
    throw new ApiError(422, "Date filtering is unavailable in the verified static demo.");
  }
  return `market=${params.get("market") ?? "*"}&family=${params.get("family") ?? "*"}`;
}

function boundedInteger(params: URLSearchParams, name: string, fallback: number, max: number) {
  const raw = params.get(name);
  const value = raw === null ? fallback : Number(raw);
  if (!Number.isInteger(value) || value < (name === "limit" ? 1 : 0) || value > max) {
    throw new ApiError(422, `Invalid ${name} value.`);
  }
  return value;
}

function scenarioKey(params: URLSearchParams): string {
  const low = Number(params.get("capture_low") ?? "0.20");
  const high = Number(params.get("capture_high") ?? "0.50");
  const onGrid = (value: number) =>
    Number.isFinite(value) && value >= 0 && value <= 1 && Math.abs(value * 20 - Math.round(value * 20)) < 1e-8;
  if (!onGrid(low) || !onGrid(high) || low > high) {
    throw new ApiError(
      422,
      "Static pricing scenarios require 5-point capture increments with low not above high.",
    );
  }
  return `${low.toFixed(2)}:${high.toFixed(2)}`;
}

/** Resolve an API-shaped request from the verified aggregate-only snapshot. */
export async function staticGet<T>(path: string): Promise<T> {
  const snapshot = await loadSnapshot();
  const url = new URL(path, "https://portfolio.invalid");
  const filtered = () => {
    const value = snapshot.filtered[selectionKey(url.searchParams)];
    if (!value) throw new ApiError(422, "That market or product-family filter is unavailable.");
    return value;
  };

  let result: unknown;
  switch (url.pathname) {
    case "/api/metadata":
      result = snapshot.metadata;
      break;
    case "/api/overview":
      result = filtered().overview;
      break;
    case "/api/revenue/trend":
      result = filtered().revenue_trend;
      break;
    case "/api/revenue/by-family":
      result = filtered().revenue_by_family;
      break;
    case "/api/revenue/by-market":
      result = filtered().revenue_by_market;
      break;
    case "/api/products/top": {
      const source = filtered().products;
      const limit = boundedInteger(url.searchParams, "limit", 20, 200);
      const offset = boundedInteger(url.searchParams, "offset", 0, 100_000);
      result = {
        filters: source.filters,
        items: source.items.slice(offset, offset + limit),
        total: source.total,
        limit,
        offset,
      };
      break;
    }
    case "/api/revenue/bridge": {
      const lens = url.searchParams.get("lens") ?? "product";
      result = snapshot.fixed[`bridge_${lens}`];
      break;
    }
    case "/api/products/classification":
      result = snapshot.fixed.classification;
      break;
    case "/api/customers/segments":
      result = snapshot.fixed.segments;
      break;
    case "/api/customers/cohorts":
      result = snapshot.fixed.cohorts;
      break;
    case "/api/customers/clv":
      result = snapshot.fixed.clv;
      break;
    case "/api/pricing/opportunities":
      result = snapshot.opportunities[scenarioKey(url.searchParams)];
      break;
    case "/api/pricing/dispersion":
      result = snapshot.fixed.dispersion;
      break;
    case "/api/pricing/price-response":
      result = snapshot.fixed.price_response;
      break;
    case "/api/experiments/summary":
      result = snapshot.fixed.experiment_summary;
      break;
    case "/api/experiments/power-curve":
      result = snapshot.fixed.power_curve;
      break;
    case "/api/executive/summary":
      result = snapshot.fixed.executive;
      break;
    default:
      throw new ApiError(404, "This analysis is not included in the static demo.");
  }
  if (result === undefined) throw new ApiError(404, "Static analysis response unavailable.");
  return result as T;
}

export function resetStaticSnapshotForTests() {
  snapshotPromise = undefined;
}
