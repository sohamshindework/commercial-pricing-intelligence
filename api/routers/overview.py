"""Commercial overview: filtered headline KPIs."""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends

from api.deps import applied, get_con, get_filters
from api.schemas import AppliedFilters, OverviewKpis, OverviewResponse
from commercial_intelligence.reporting import queries
from commercial_intelligence.reporting.queries import Filters

router = APIRouter(prefix="/api/overview", tags=["overview"])


@router.get("", response_model=OverviewResponse)
def overview(
    con: duckdb.DuckDBPyConnection = Depends(get_con),
    f: Filters = Depends(get_filters),
) -> OverviewResponse:
    return OverviewResponse(
        filters=AppliedFilters(**applied(f)),
        kpis=OverviewKpis(**queries.overview_kpis(con, f)),
    )
