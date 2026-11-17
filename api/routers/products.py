"""Products: paginated, filtered top products (demonstrates pagination)."""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import applied, get_con, get_filters
from api.schemas import (
    AppliedFilters,
    ClassificationResponse,
    ClassMetric,
    PagedProducts,
    PerClassRow,
    Product,
)
from commercial_intelligence.products.taxonomy import code_to_name
from commercial_intelligence.reporting import exports, queries
from commercial_intelligence.reporting.queries import Filters

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/classification", response_model=ClassificationResponse)
def classification() -> ClassificationResponse:
    """Product-family classification quality on the held-out test set (fixed period)."""
    try:
        metrics = exports.product_metrics()
        per_class = exports.per_class_baseline()
    except exports.MissingExportError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    names = code_to_name()
    chosen = metrics.sort_values("macro_f1", ascending=False)["method"].iloc[0]
    return ClassificationResponse(
        period_note=(
            "TF-IDF + logistic regression evaluated on the held-out test set. "
            "The former LLM comparison was withdrawn because its cassette was label-derived."
        ),
        chosen_method=str(chosen),
        metrics=[ClassMetric(**r._asdict()) for r in metrics.itertuples(index=False)],
        per_class=[
            PerClassRow(
                family_code=r.family_code, name=names.get(r.family_code, r.family_code),
                precision=float(r.precision), recall=float(r.recall),
                f1=float(r.f1), support=int(r.support),
            )
            for r in per_class.itertuples(index=False)
        ],
    )


@router.get("/top", response_model=PagedProducts)
def top(
    con: duckdb.DuckDBPyConnection = Depends(get_con),
    f: Filters = Depends(get_filters),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0, le=100_000),
) -> PagedProducts:
    items, total = queries.top_products(con, f, limit, offset)
    return PagedProducts(
        filters=AppliedFilters(**applied(f)),
        items=[Product(**i) for i in items],
        total=total, limit=limit, offset=offset,
    )
