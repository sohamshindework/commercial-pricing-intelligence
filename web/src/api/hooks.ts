// TanStack Query hooks. Query keys include the filters so views refetch on change.

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { apiGet, filtersToQuery } from "./client";
import type {
  ClassificationResponse,
  ClvResponse,
  CohortsResponse,
  DispersionResponse,
  ExecutiveResponse,
  ExperimentSummary,
  FilterValues,
  Metadata,
  OpportunitiesResponse,
  OverviewResponse,
  PagedProducts,
  PowerCurveResponse,
  PriceResponseResponse,
  RevenueBridgeResponse,
  RevenueByFamilyResponse,
  RevenueByMarketResponse,
  RevenueTrendResponse,
  SegmentsResponse,
} from "./types";

export function useMetadata() {
  return useQuery({
    queryKey: ["metadata"],
    queryFn: () => apiGet<Metadata>("/api/metadata"),
    staleTime: Infinity,
  });
}

export function useOverview(filters: FilterValues) {
  return useQuery({
    queryKey: ["overview", filters],
    queryFn: () => apiGet<OverviewResponse>(`/api/overview${filtersToQuery(filters)}`),
  });
}

export function useRevenueTrend(filters: FilterValues) {
  return useQuery({
    queryKey: ["revenue-trend", filters],
    queryFn: () =>
      apiGet<RevenueTrendResponse>(`/api/revenue/trend${filtersToQuery(filters)}`),
  });
}

export function useRevenueBridge(lens: string) {
  return useQuery({
    queryKey: ["revenue-bridge", lens],
    queryFn: () => apiGet<RevenueBridgeResponse>(`/api/revenue/bridge?lens=${lens}`),
  });
}

export function useRevenueByFamily(filters: FilterValues) {
  return useQuery({
    queryKey: ["revenue-by-family", filters],
    queryFn: () =>
      apiGet<RevenueByFamilyResponse>(`/api/revenue/by-family${filtersToQuery(filters)}`),
  });
}

export function useRevenueByMarket(filters: FilterValues) {
  return useQuery({
    queryKey: ["revenue-by-market", filters],
    queryFn: () =>
      apiGet<RevenueByMarketResponse>(`/api/revenue/by-market${filtersToQuery(filters)}`),
  });
}

export function useTopProducts(filters: FilterValues, limit: number, offset: number) {
  const base = filtersToQuery(filters);
  const sep = base ? "&" : "?";
  return useQuery({
    queryKey: ["top-products", filters, limit, offset],
    queryFn: () =>
      apiGet<PagedProducts>(`/api/products/top${base}${sep}limit=${limit}&offset=${offset}`),
    placeholderData: keepPreviousData,
  });
}

export function useClassification() {
  return useQuery({
    queryKey: ["classification"],
    queryFn: () => apiGet<ClassificationResponse>("/api/products/classification"),
    staleTime: Infinity,
  });
}

const FIXED = { staleTime: Infinity } as const;

export function useSegments() {
  return useQuery({
    queryKey: ["segments"],
    queryFn: () => apiGet<SegmentsResponse>("/api/customers/segments"),
    ...FIXED,
  });
}

export function useCohorts() {
  return useQuery({
    queryKey: ["cohorts"],
    queryFn: () => apiGet<CohortsResponse>("/api/customers/cohorts"),
    ...FIXED,
  });
}

export function useClv() {
  return useQuery({
    queryKey: ["clv"],
    queryFn: () => apiGet<ClvResponse>("/api/customers/clv"),
    ...FIXED,
  });
}

export function useOpportunities(captureLow: number, captureHigh: number) {
  return useQuery({
    queryKey: ["opportunities", captureLow, captureHigh],
    queryFn: () =>
      apiGet<OpportunitiesResponse>(
        `/api/pricing/opportunities?capture_low=${captureLow}&capture_high=${captureHigh}`,
      ),
    placeholderData: keepPreviousData,
  });
}

export function useDispersion() {
  return useQuery({
    queryKey: ["dispersion"],
    queryFn: () => apiGet<DispersionResponse>("/api/pricing/dispersion?limit=15"),
    ...FIXED,
  });
}

export function usePriceResponse() {
  return useQuery({
    queryKey: ["price-response"],
    queryFn: () => apiGet<PriceResponseResponse>("/api/pricing/price-response"),
    ...FIXED,
  });
}

export function useExperimentSummary() {
  return useQuery({
    queryKey: ["experiment-summary"],
    queryFn: () => apiGet<ExperimentSummary>("/api/experiments/summary"),
    ...FIXED,
  });
}

export function usePowerCurve() {
  return useQuery({
    queryKey: ["power-curve"],
    queryFn: () => apiGet<PowerCurveResponse>("/api/experiments/power-curve"),
    ...FIXED,
  });
}

export function useExecutive() {
  return useQuery({
    queryKey: ["executive"],
    queryFn: () => apiGet<ExecutiveResponse>("/api/executive/summary"),
    ...FIXED,
  });
}
