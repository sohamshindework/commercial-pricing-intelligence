"""Revenue: filtered trend and by-family (interactive) + fixed-period bridge."""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import applied, get_con, get_filters
from api.schemas import (
    AppliedFilters,
    BridgeComponent,
    FamilyRevenue,
    MarketRevenue,
    RevenueBridgeResponse,
    RevenueByFamilyResponse,
    RevenueByMarketResponse,
    RevenueTrendResponse,
    TrendPoint,
)
from commercial_intelligence.reporting import exports, queries
from commercial_intelligence.reporting.queries import Filters

router = APIRouter(prefix="/api/revenue", tags=["revenue"])


@router.get("/trend", response_model=RevenueTrendResponse)
def trend(
    con: duckdb.DuckDBPyConnection = Depends(get_con),
    f: Filters = Depends(get_filters),
) -> RevenueTrendResponse:
    return RevenueTrendResponse(
        filters=AppliedFilters(**applied(f)),
        points=[TrendPoint(**p) for p in queries.revenue_trend(con, f)],
    )


@router.get("/by-family", response_model=RevenueByFamilyResponse)
def by_family(
    con: duckdb.DuckDBPyConnection = Depends(get_con),
    f: Filters = Depends(get_filters),
) -> RevenueByFamilyResponse:
    return RevenueByFamilyResponse(
        filters=AppliedFilters(**applied(f)),
        items=[FamilyRevenue(**r) for r in queries.revenue_by_family(con, f)],
    )


@router.get("/by-market", response_model=RevenueByMarketResponse)
def by_market(
    con: duckdb.DuckDBPyConnection = Depends(get_con),
    f: Filters = Depends(get_filters),
) -> RevenueByMarketResponse:
    return RevenueByMarketResponse(
        filters=AppliedFilters(**applied(f)),
        items=[MarketRevenue(**r) for r in queries.revenue_by_market(con, f)],
    )


@router.get("/bridge", response_model=RevenueBridgeResponse)
def bridge(lens: str = Query("product", pattern="^(product|customer|geography)$")):
    """Fixed-period year-on-year decomposition (not affected by the global filters)."""
    try:
        b = exports.bridge(lens)
    except exports.MissingExportError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    if b.empty:
        raise HTTPException(status_code=404, detail=f"No bridge for lens {lens!r}.")
    comps = [
        BridgeComponent(component=r.component, value_gbp=float(r.value_gbp),
                        kind=r.kind, step_order=int(r.step_order))
        for r in b.itertuples()
    ]
    return RevenueBridgeResponse(
        lens=lens, comparison_label=str(b["comparison_label"].iloc[0]), components=comps
    )
