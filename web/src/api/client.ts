// Typed data wrapper. Local mode calls FastAPI; demo mode resolves the same
// contracts from a verified aggregate-only snapshot.

import type { FilterValues } from "./types";

const BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");
export const IS_STATIC_DEMO = import.meta.env.VITE_DATA_MODE === "static";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function filtersToQuery(f: FilterValues): string {
  const p = new URLSearchParams();
  if (f.start) p.set("start", f.start);
  if (f.end) p.set("end", f.end);
  if (f.market) p.set("market", f.market);
  if (f.family) p.set("family", f.family);
  const s = p.toString();
  return s ? `?${s}` : "";
}

export async function apiGet<T>(path: string): Promise<T> {
  if (IS_STATIC_DEMO) {
    const { staticGet } = await import("./staticData");
    return staticGet<T>(path);
  }
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { headers: { Accept: "application/json" } });
  } catch {
    throw new ApiError(0, "Could not reach the analytics service.");
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status}).`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}
