"""Customer analytics: segments, cohort retention, CLV — all fixed-period model outputs."""

from __future__ import annotations

import numpy as np
from fastapi import APIRouter, HTTPException

from api.schemas import (
    ClvBin,
    ClvMetric,
    ClvResponse,
    CohortPoint,
    CohortRow,
    CohortsResponse,
    RetentionCurvePoint,
    Segment,
    SegmentsResponse,
)
from commercial_intelligence.reporting import exports

router = APIRouter(prefix="/api/customers", tags=["customers"])


def _guard(fn):
    try:
        return fn()
    except exports.MissingExportError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@router.get("/segments", response_model=SegmentsResponse)
def segments() -> SegmentsResponse:
    df = _guard(exports.segment_summary)
    return SegmentsResponse(
        items=[
            Segment(segment=r.rfm_segment, customers=int(r.customers), monetary=float(r.monetary))
            for r in df.itertuples(index=False)
        ]
    )


@router.get("/cohorts", response_model=CohortsResponse)
def cohorts() -> CohortsResponse:
    rates = _guard(exports.cohort_rates)
    counts = _guard(exports.cohort_counts)
    offset_cols = [c for c in rates.columns if str(c).isdigit()]
    offsets = sorted(int(c) for c in offset_cols)

    # Cohort size = the offset-0 count column.
    counts_indexed = counts.set_index("cohort_month")
    rows = []
    for _, r in rates.iterrows():
        month = str(r["cohort_month"])[:7]
        points = [
            CohortPoint(offset=int(c), rate=float(r[c]))
            for c in offset_cols
            if r[c] == r[c]  # not NaN
        ]
        size = int(counts_indexed.loc[r["cohort_month"], "0"]) if "0" in counts.columns else 0
        rows.append(CohortRow(cohort_month=month, size=size, points=points))

    curve_df = _guard(exports.retention_curve)
    curve = [
        RetentionCurvePoint(
            offset=int(c.month_offset), retention=float(c.avg_retention), cohorts=int(c.cohorts)
        )
        for c in curve_df.itertuples(index=False)
    ]
    return CohortsResponse(offsets=offsets, cohorts=rows, curve=curve)


@router.get("/clv", response_model=ClvResponse)
def clv() -> ClvResponse:
    metrics = _guard(exports.clv_metrics)
    customers = _guard(exports.clv_customers)
    winner = metrics.sort_values("mae")["method"].iloc[0]

    values = customers["expected_clv_horizon"].to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if (values < 0).any():
        raise HTTPException(
            status_code=503,
            detail="Customer-value export failed validation; rebuild the analytical outputs.",
        )
    hi = float(np.quantile(values, 0.97)) if len(values) else 1.0
    clipped = np.minimum(values, hi)
    counts, edges = np.histogram(clipped, bins=12, range=(0, max(hi, 1.0)))
    distribution = [
        ClvBin(lower=float(edges[i]), upper=float(edges[i + 1]), count=int(counts[i]))
        for i in range(len(counts))
    ]
    return ClvResponse(
        period_note=(
            "180-day future repeat value in GBP. Methods are selected out of sample on "
            "complete holdout value against a historical-value baseline."
        ),
        winner=str(winner),
        metrics=[ClvMetric(**r._asdict()) for r in metrics.itertuples(index=False)],
        distribution=distribution,
        avg_clv=float(values.mean()) if len(values) else 0.0,
        total_clv=float(values.sum()) if len(values) else 0.0,
    )
