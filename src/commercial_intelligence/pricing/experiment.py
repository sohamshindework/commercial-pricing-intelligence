"""SKU-randomised pricing experiment design and independently checked power."""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy import stats
from statsmodels.stats.power import TTestIndPower


@dataclass
class PowerResult:
    alpha: float
    power: float
    mde_relative: float
    baseline_mean: float
    baseline_sd: float
    effect_size_d: float
    n_per_group: int          # independent randomisation units (SKUs) per arm
    n_total: int


def effect_size(baseline_mean: float, baseline_sd: float, mde_relative: float) -> float:
    """Cohen's d for a relative shift in the mean of the primary metric."""
    if baseline_sd <= 0:
        raise ValueError("baseline_sd must be positive")
    return abs(mde_relative * baseline_mean) / baseline_sd


def sample_size_statsmodels(
    baseline_mean: float, baseline_sd: float, mde_relative: float,
    alpha: float = 0.05, power: float = 0.80,
) -> PowerResult:
    d = effect_size(baseline_mean, baseline_sd, mde_relative)
    n = TTestIndPower().solve_power(effect_size=d, alpha=alpha, power=power, ratio=1.0)
    n_per = int(math.ceil(n))
    return PowerResult(alpha, power, mde_relative, baseline_mean, baseline_sd, d, n_per, 2 * n_per)


def sample_size_normal_approx(
    baseline_mean: float, baseline_sd: float, mde_relative: float,
    alpha: float = 0.05, power: float = 0.80,
) -> float:
    """Closed-form two-sample size per group: n = 2 (z_{1-a/2} + z_{1-b})^2 / d^2."""
    d = effect_size(baseline_mean, baseline_sd, mde_relative)
    z_a = stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(power)
    return 2 * (z_a + z_b) ** 2 / d**2


def minimum_detectable_effect(
    baseline_mean: float, baseline_sd: float, n_per_group: int,
    alpha: float = 0.05, power: float = 0.80,
) -> float:
    """Smallest relative effect detectable with the given per-arm sample size."""
    d = TTestIndPower().solve_power(
        nobs1=n_per_group, alpha=alpha, power=power, ratio=1.0
    )
    return float(d * baseline_sd / baseline_mean)


@dataclass
class ExperimentDesign:
    title: str
    hypothesis: str
    unit_of_randomisation: str
    primary_metric: str
    guardrail_metrics: list[str]
    risks: list[str]
    decision_rule: str
    power: PowerResult
    eligible_products: int
    available_products_per_arm: int
    required_products_per_arm: int
    mde_available_unadjusted: float
    mde_available_adjusted: float
    preperiod_correlation: float
    variance_reduction: float
    adequately_powered: bool
    duration_weeks: int


def design_price_experiment(
    power: PowerResult,
    *,
    eligible_products: int,
    weeks_available: int,
    mde_available_unadjusted: float,
    mde_available_adjusted: float,
    preperiod_correlation: float,
) -> ExperimentDesign:
    available_per_arm = eligible_products // 2
    variance_reduction = preperiod_correlation**2
    adequately_powered = available_per_arm >= power.n_per_group
    return ExperimentDesign(
        title="Price-realisation floor on high-dispersion products",
        hypothesis=(
            "Introducing a price floor (limiting how far below the median list price a "
            "product may be sold) raises average weekly gross sales revenue per SKU without a "
            "material fall in "
            "units. This is a causal hypothesis to be tested: the observational analysis "
            "establishes only an association, and this randomised test is what would confirm "
            "an effect."
        ),
        unit_of_randomisation=(
            "Product (SKU). Candidate high-dispersion products are randomised to a treatment "
            "arm (price floor applied) or a control arm (unchanged), stratified by family and "
            "revenue decile."
        ),
        primary_metric=(
            f"Average weekly gross sales revenue per assigned SKU over {weeks_available} weeks, "
            "including zero-sales weeks. Analyse one outcome per SKU with pre-period revenue "
            "and randomisation strata as covariates."
        ),
        guardrail_metrics=[
            "Units sold per SKU-week (including zeros; volume must not fall materially).",
            "Sale-invoice count per SKU-week.",
            "Cancellation value and cancellation-invoice rate.",
        ],
        risks=[
            "Contamination: customers substitute between treated and control products "
            "(mitigate by randomising whole sub-categories where substitution is high).",
            "Novelty / promotion-timing effects: run across whole weeks, avoid launch spikes.",
            "Repeated weeks within a SKU are not independent; aggregate the full test window "
            "to one SKU outcome and use the SKU as the analysis unit.",
            "Seasonality: run treatment and control concurrently across whole weeks.",
        ],
        decision_rule=(
            f"Estimate the intention-to-treat effect with SKU-level ANCOVA. Claim a positive "
            f"effect only if the two-sided p-value is below {power.alpha}, the confidence "
            "interval excludes zero, and no pre-registered guardrail is breached. Do not use "
            "the observational scenario range as the success threshold."
        ),
        power=power,
        eligible_products=eligible_products,
        available_products_per_arm=available_per_arm,
        required_products_per_arm=power.n_per_group,
        mde_available_unadjusted=mde_available_unadjusted,
        mde_available_adjusted=mde_available_adjusted,
        preperiod_correlation=preperiod_correlation,
        variance_reduction=variance_reduction,
        adequately_powered=adequately_powered,
        duration_weeks=weeks_available,
    )
