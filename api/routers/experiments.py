"""Experiment sizing: summary and a power curve computed from the data's variance."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas import ExperimentSummary, PowerCurveResponse, PowerPoint
from commercial_intelligence.pricing.experiment import minimum_detectable_effect
from commercial_intelligence.reporting import exports

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


def _summary_row():
    try:
        return exports.experiment_summary().iloc[0]
    except exports.MissingExportError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@router.get("/summary", response_model=ExperimentSummary)
def summary() -> ExperimentSummary:
    r = _summary_row()
    return ExperimentSummary(
        metric=str(r["metric"]),
        randomisation_unit=str(r["randomisation_unit"]),
        analysis_unit=str(r["analysis_unit"]),
        baseline_mean_gbp=float(r["baseline_mean_gbp"]),
        baseline_sd_gbp=float(r["baseline_sd_gbp"]),
        cuped_residual_sd_gbp=float(r["cuped_residual_sd_gbp"]),
        preperiod_correlation=float(r["preperiod_correlation"]),
        variance_reduction=float(r["variance_reduction"]),
        target_mde_relative=float(r["target_mde_relative"]),
        alpha=float(r["alpha"]),
        power=float(r["power"]),
        eligible_products=int(r["eligible_products"]),
        available_products_per_arm=int(r["available_products_per_arm"]),
        required_products_per_arm=int(r["required_products_per_arm"]),
        mde_available_unadjusted=float(r["mde_available_unadjusted"]),
        mde_available_relative=float(r["mde_available_relative"]),
        adequately_powered=bool(r["adequately_powered"]),
        duration_weeks=int(r["duration_weeks"]),
    )


@router.get("/power-curve", response_model=PowerCurveResponse)
def power_curve() -> PowerCurveResponse:
    """Minimum detectable effect vs per-arm sample size, at the configured power/alpha.

    Computed with statsmodels from the SKU-level CUPED residual variance. Repeated
    weeks are aggregated before analysis; sample size means independent SKUs per arm.
    """
    r = _summary_row()
    mean, sd = float(r["baseline_mean_gbp"]), float(r["cuped_residual_sd_gbp"])
    alpha, power = float(r["alpha"]), float(r["power"])
    available = int(r["available_products_per_arm"])
    required = int(r["required_products_per_arm"])
    grid = sorted({100, 250, 500, 1000, available, required})
    points = [
        PowerPoint(
            n_per_group=n,
            mde_relative=float(minimum_detectable_effect(mean, sd, n, alpha, power)),
        )
        for n in grid
    ]
    return PowerCurveResponse(alpha=alpha, power=power, points=points)
