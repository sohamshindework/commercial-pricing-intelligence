"""Pydantic request/response schemas for the API."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class FamilyRef(BaseModel):
    family_code: str
    name: str


class Metadata(BaseModel):
    date_min: date
    date_max: date
    markets: list[str]
    families: list[FamilyRef]
    currency: str = "GBP"
    # Endpoints whose results are fixed-period and must not appear to react to
    # the global filters (the UI labels these).
    fixed_period_endpoints: list[str]


class AppliedFilters(BaseModel):
    start: date | None = None
    end: date | None = None
    market: str | None = None
    family_code: str | None = None


class OverviewKpis(BaseModel):
    net_revenue: float
    gross_revenue: float
    cancellations: float
    sale_invoices: int
    cancellation_invoices: int
    all_invoices: int
    active_customers: int
    units_sold: int
    gross_sales_aov: float
    guest_revenue_pct: float


class OverviewResponse(BaseModel):
    filters: AppliedFilters
    kpis: OverviewKpis


class TrendPoint(BaseModel):
    year_month: str
    net_revenue: float
    sale_invoices: int
    cancellation_invoices: int
    is_partial_month: bool


class RevenueTrendResponse(BaseModel):
    filters: AppliedFilters
    points: list[TrendPoint]


class FamilyRevenue(BaseModel):
    family_code: str
    net_revenue: float


class RevenueByFamilyResponse(BaseModel):
    filters: AppliedFilters
    items: list[FamilyRevenue]


class BridgeComponent(BaseModel):
    component: str
    value_gbp: float
    kind: str
    step_order: int


class RevenueBridgeResponse(BaseModel):
    lens: str
    comparison_label: str
    interactive: bool = Field(
        default=False,
        description="Fixed-period decomposition; not affected by the global filters.",
    )
    components: list[BridgeComponent]


class MarketRevenue(BaseModel):
    market: str
    net_revenue: float
    sale_invoices: int
    cancellation_invoices: int


class RevenueByMarketResponse(BaseModel):
    filters: AppliedFilters
    items: list[MarketRevenue]


class Product(BaseModel):
    product_key: str
    product_name: str
    family_code: str
    net_revenue: float
    units: int


class ClassMetric(BaseModel):
    method: str
    accuracy: float
    macro_f1: float
    weighted_f1: float
    n: int


class PerClassRow(BaseModel):
    family_code: str
    name: str
    precision: float
    recall: float
    f1: float
    support: int


class ClassificationResponse(BaseModel):
    interactive: bool = Field(default=False)
    period_note: str
    chosen_method: str
    metrics: list[ClassMetric]
    per_class: list[PerClassRow]


# ---- customers (fixed-period model outputs) --------------------------------
class Segment(BaseModel):
    segment: str
    customers: int
    monetary: float


class SegmentsResponse(BaseModel):
    interactive: bool = Field(default=False)
    items: list[Segment]


class CohortPoint(BaseModel):
    offset: int
    rate: float


class CohortRow(BaseModel):
    cohort_month: str
    size: int
    points: list[CohortPoint]


class RetentionCurvePoint(BaseModel):
    offset: int
    retention: float
    cohorts: int


class CohortsResponse(BaseModel):
    interactive: bool = Field(default=False)
    offsets: list[int]
    cohorts: list[CohortRow]
    curve: list[RetentionCurvePoint]


class ClvMetric(BaseModel):
    method: str
    mae: float
    rmse: float
    predicted_total: float
    actual_total: float


class ClvBin(BaseModel):
    lower: float
    upper: float
    count: int


class ClvResponse(BaseModel):
    interactive: bool = Field(default=False)
    period_note: str
    winner: str
    metrics: list[ClvMetric]
    distribution: list[ClvBin]
    avg_clv: float
    total_clv: float


# ---- pricing (fixed-period + scenario inputs) ------------------------------
class Opportunity(BaseModel):
    key: str
    name: str
    measured_gap_gbp: float
    impact_low_gbp: float
    impact_high_gbp: float
    impact_low_pct_rev: float
    impact_high_pct_rev: float
    margin_low_gbp: float
    margin_high_gbp: float


class OpportunitiesResponse(BaseModel):
    capture_low: float
    capture_high: float
    assumed_cost_ratio: float
    net_revenue: float
    items: list[Opportunity]


class DispersionProduct(BaseModel):
    product_key: str
    product_name: str
    price_min: float
    price_median: float
    price_max: float
    price_cv: float
    revenue: float


class DispersionResponse(BaseModel):
    interactive: bool = Field(default=False)
    items: list[DispersionProduct]


class PriceResponseRow(BaseModel):
    family_code: str
    name: str
    within_slope: float
    within_ci_low: float
    within_ci_high: float
    n_lines: int
    n_products: int


class PriceResponseResponse(BaseModel):
    interactive: bool = Field(default=False)
    note: str
    items: list[PriceResponseRow]


# ---- experiments -----------------------------------------------------------
class ExperimentSummary(BaseModel):
    metric: str
    randomisation_unit: str
    analysis_unit: str
    baseline_mean_gbp: float
    baseline_sd_gbp: float
    cuped_residual_sd_gbp: float
    preperiod_correlation: float
    variance_reduction: float
    target_mde_relative: float
    alpha: float
    power: float
    eligible_products: int
    available_products_per_arm: int
    required_products_per_arm: int
    mde_available_unadjusted: float
    mde_available_relative: float
    adequately_powered: bool
    duration_weeks: int


class PowerPoint(BaseModel):
    n_per_group: int
    mde_relative: float


class PowerCurveResponse(BaseModel):
    alpha: float
    power: float
    points: list[PowerPoint]


# ---- executive summary -----------------------------------------------------
class ExecHeadline(BaseModel):
    net_revenue: float
    sale_invoices: int
    cancellation_invoices: int
    gross_sales_aov: float
    active_customers: int
    yoy_pct: float
    yoy_label: str


class Recommendation(BaseModel):
    priority: int
    action: str
    evidence: str
    scenario_impact: str
    success_metric: str
    confidence: str


class MonitoringKpi(BaseModel):
    name: str
    definition: str


class ExecutiveResponse(BaseModel):
    interactive: bool = Field(default=False)
    situation: str
    headline: ExecHeadline
    recommendations: list[Recommendation]
    monitoring_kpis: list[MonitoringKpi]
    limitations: list[str]


class PagedProducts(BaseModel):
    filters: AppliedFilters
    items: list[Product]
    total: int
    limit: int
    offset: int
