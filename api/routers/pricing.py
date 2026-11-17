"""Pricing: opportunities (with scenario capture inputs), dispersion, price response."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from api.schemas import (
    DispersionProduct,
    DispersionResponse,
    OpportunitiesResponse,
    Opportunity,
    PriceResponseResponse,
    PriceResponseRow,
)
from commercial_intelligence.common.config import load_settings
from commercial_intelligence.products.taxonomy import code_to_name
from commercial_intelligence.reporting import exports

router = APIRouter(prefix="/api/pricing", tags=["pricing"])


def _guard(fn):
    try:
        return fn()
    except exports.MissingExportError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


def _capture(
    capture_low: float = Query(0.20, ge=0.0, le=1.0),
    capture_high: float = Query(0.50, ge=0.0, le=1.0),
) -> tuple[float, float]:
    if capture_low > capture_high:
        raise HTTPException(status_code=422, detail="capture_low must be <= capture_high.")
    return capture_low, capture_high


@router.get("/opportunities", response_model=OpportunitiesResponse)
def opportunities(capture: tuple[float, float] = Depends(_capture)) -> OpportunitiesResponse:
    """Revenue-opportunity ranges = measured gap x the scenario capture rate.

    The gap is a fixed measured figure; the capture rate is a stated assumption the
    user varies. Ranges are recomputed here (never a causal or profit claim).
    """
    low, high = capture
    cfg = load_settings()["pricing"]
    cost_ratio = float(cfg["assumed_cost_ratio"])
    opp = _guard(exports.opportunities)
    recon = _guard(exports.reconciliation).set_index("measure")["python_value"]
    net_rev = float(recon["net_revenue"])

    items = []
    for r in opp.itertuples(index=False):
        gap = float(r.measured_gap_gbp)
        lo, hi = gap * low, gap * high
        items.append(
            Opportunity(
                key=r.key, name=r.name, measured_gap_gbp=gap,
                impact_low_gbp=lo, impact_high_gbp=hi,
                impact_low_pct_rev=lo / net_rev * 100 if net_rev else 0.0,
                impact_high_pct_rev=hi / net_rev * 100 if net_rev else 0.0,
                margin_low_gbp=lo * (1 - cost_ratio), margin_high_gbp=hi * (1 - cost_ratio),
            )
        )
    return OpportunitiesResponse(
        capture_low=low, capture_high=high, assumed_cost_ratio=cost_ratio,
        net_revenue=net_rev, items=items,
    )


@router.get("/dispersion", response_model=DispersionResponse)
def dispersion(limit: int = Query(15, ge=1, le=100)) -> DispersionResponse:
    df = _guard(exports.price_dispersion)
    df = df[df["n_prices"] > 1].nlargest(limit, "revenue")
    return DispersionResponse(
        items=[
            DispersionProduct(
                product_key=r.product_key, product_name=r.product_name,
                price_min=float(r.price_min), price_median=float(r.price_median),
                price_max=float(r.price_max), price_cv=float(r.price_cv),
                revenue=float(r.revenue),
            )
            for r in df.itertuples(index=False)
        ]
    )


@router.get("/price-response", response_model=PriceResponseResponse)
def price_response() -> PriceResponseResponse:
    df = _guard(exports.price_response)
    names = code_to_name()
    return PriceResponseResponse(
        note=(
            "Within-product log-log association between unit price and quantity. "
            "Descriptive only — confounded by quantity-break pricing and seasonality; "
            "not a price elasticity."
        ),
        items=[
            PriceResponseRow(
                family_code=r.family_code, name=names.get(r.family_code, r.family_code),
                within_slope=float(r.within_slope), within_ci_low=float(r.within_ci_low),
                within_ci_high=float(r.within_ci_high),
                n_lines=int(r.n_lines), n_products=int(r.n_products),
            )
            for r in df.itertuples(index=False)
        ],
    )
