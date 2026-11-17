// Mirrors the FastAPI Pydantic schemas (api/schemas.py).

export interface FamilyRef {
  family_code: string;
  name: string;
}

export interface Metadata {
  date_min: string;
  date_max: string;
  markets: string[];
  families: FamilyRef[];
  currency: string;
  fixed_period_endpoints: string[];
}

export interface AppliedFilters {
  start: string | null;
  end: string | null;
  market: string | null;
  family_code: string | null;
}

export interface OverviewKpis {
  net_revenue: number;
  gross_revenue: number;
  cancellations: number;
  sale_invoices: number;
  cancellation_invoices: number;
  all_invoices: number;
  active_customers: number;
  units_sold: number;
  gross_sales_aov: number;
  guest_revenue_pct: number;
}

export interface OverviewResponse {
  filters: AppliedFilters;
  kpis: OverviewKpis;
}

export interface TrendPoint {
  year_month: string;
  net_revenue: number;
  sale_invoices: number;
  cancellation_invoices: number;
  is_partial_month: boolean;
}

export interface RevenueTrendResponse {
  filters: AppliedFilters;
  points: TrendPoint[];
}

export interface BridgeComponent {
  component: string;
  value_gbp: number;
  kind: string;
  step_order: number;
}

export interface RevenueBridgeResponse {
  lens: string;
  comparison_label: string;
  interactive: boolean;
  components: BridgeComponent[];
}

export interface FilterValues {
  start?: string;
  end?: string;
  market?: string;
  family?: string;
}

export interface FamilyRevenue {
  family_code: string;
  net_revenue: number;
}

export interface RevenueByFamilyResponse {
  filters: AppliedFilters;
  items: FamilyRevenue[];
}

export interface MarketRevenue {
  market: string;
  net_revenue: number;
  sale_invoices: number;
  cancellation_invoices: number;
}

export interface RevenueByMarketResponse {
  filters: AppliedFilters;
  items: MarketRevenue[];
}

export interface Product {
  product_key: string;
  product_name: string;
  family_code: string;
  net_revenue: number;
  units: number;
}

export interface PagedProducts {
  filters: AppliedFilters;
  items: Product[];
  total: number;
  limit: number;
  offset: number;
}

export interface ClassMetric {
  method: string;
  accuracy: number;
  macro_f1: number;
  weighted_f1: number;
  n: number;
}

export interface PerClassRow {
  family_code: string;
  name: string;
  precision: number;
  recall: number;
  f1: number;
  support: number;
}

export interface ClassificationResponse {
  interactive: boolean;
  period_note: string;
  chosen_method: string;
  metrics: ClassMetric[];
  per_class: PerClassRow[];
}

export interface Segment {
  segment: string;
  customers: number;
  monetary: number;
}
export interface SegmentsResponse {
  interactive: boolean;
  items: Segment[];
}

export interface CohortPoint {
  offset: number;
  rate: number;
}
export interface CohortRow {
  cohort_month: string;
  size: number;
  points: CohortPoint[];
}
export interface RetentionCurvePoint {
  offset: number;
  retention: number;
  cohorts: number;
}
export interface CohortsResponse {
  interactive: boolean;
  offsets: number[];
  cohorts: CohortRow[];
  curve: RetentionCurvePoint[];
}

export interface ClvMetric {
  method: string;
  mae: number;
  rmse: number;
  predicted_total: number;
  actual_total: number;
}
export interface ClvBin {
  lower: number;
  upper: number;
  count: number;
}
export interface ClvResponse {
  interactive: boolean;
  period_note: string;
  winner: string;
  metrics: ClvMetric[];
  distribution: ClvBin[];
  avg_clv: number;
  total_clv: number;
}

export interface Opportunity {
  key: string;
  name: string;
  measured_gap_gbp: number;
  impact_low_gbp: number;
  impact_high_gbp: number;
  impact_low_pct_rev: number;
  impact_high_pct_rev: number;
  margin_low_gbp: number;
  margin_high_gbp: number;
}
export interface OpportunitiesResponse {
  capture_low: number;
  capture_high: number;
  assumed_cost_ratio: number;
  net_revenue: number;
  items: Opportunity[];
}

export interface DispersionProduct {
  product_key: string;
  product_name: string;
  price_min: number;
  price_median: number;
  price_max: number;
  price_cv: number;
  revenue: number;
}
export interface DispersionResponse {
  interactive: boolean;
  items: DispersionProduct[];
}

export interface PriceResponseRow {
  family_code: string;
  name: string;
  within_slope: number;
  within_ci_low: number;
  within_ci_high: number;
  n_lines: number;
  n_products: number;
}
export interface PriceResponseResponse {
  interactive: boolean;
  note: string;
  items: PriceResponseRow[];
}

export interface ExperimentSummary {
  metric: string;
  randomisation_unit: string;
  analysis_unit: string;
  baseline_mean_gbp: number;
  baseline_sd_gbp: number;
  cuped_residual_sd_gbp: number;
  preperiod_correlation: number;
  variance_reduction: number;
  target_mde_relative: number;
  alpha: number;
  power: number;
  eligible_products: number;
  available_products_per_arm: number;
  required_products_per_arm: number;
  mde_available_unadjusted: number;
  mde_available_relative: number;
  adequately_powered: boolean;
  duration_weeks: number;
}
export interface PowerPoint {
  n_per_group: number;
  mde_relative: number;
}
export interface PowerCurveResponse {
  alpha: number;
  power: number;
  points: PowerPoint[];
}

export interface ExecHeadline {
  net_revenue: number;
  sale_invoices: number;
  cancellation_invoices: number;
  gross_sales_aov: number;
  active_customers: number;
  yoy_pct: number;
  yoy_label: string;
}
export interface Recommendation {
  priority: number;
  action: string;
  evidence: string;
  scenario_impact: string;
  success_metric: string;
  confidence: string;
}
export interface MonitoringKpi {
  name: string;
  definition: string;
}
export interface ExecutiveResponse {
  interactive: boolean;
  situation: string;
  headline: ExecHeadline;
  recommendations: Recommendation[];
  monitoring_kpis: MonitoringKpi[];
  limitations: string[];
}
