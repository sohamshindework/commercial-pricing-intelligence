"""Metadata: filter options and the data boundaries the UI needs."""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends

from api.deps import get_con
from api.schemas import FamilyRef, Metadata
from commercial_intelligence.products.taxonomy import code_to_name
from commercial_intelligence.reporting import queries

router = APIRouter(prefix="/api/metadata", tags=["metadata"])

# Endpoints whose results are fixed-period (CLV holdout, classification test set,
# revenue decomposition) and must not appear to react to the global filters.
FIXED_PERIOD = [
    "/api/revenue/bridge",
    "/api/products/classification",
    "/api/customers/segments",
    "/api/customers/cohorts",
    "/api/customers/clv",
    "/api/pricing/dispersion",
    "/api/pricing/price-response",
]


@router.get("", response_model=Metadata)
def metadata(con: duckdb.DuckDBPyConnection = Depends(get_con)) -> Metadata:
    lo, hi = queries.date_bounds(con)
    names = code_to_name()
    families = [
        FamilyRef(family_code=f["family_code"], name=names.get(f["family_code"], f["family_code"]))
        for f in queries.families(con)
    ]
    return Metadata(
        date_min=lo,
        date_max=hi,
        markets=queries.markets(con),
        families=families,
        fixed_period_endpoints=FIXED_PERIOD,
    )
