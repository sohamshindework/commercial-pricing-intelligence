"""Shared FastAPI dependencies: warehouse connection and validated filters."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from threading import BoundedSemaphore, Timer

import duckdb
from fastapi import HTTPException, Query

from api.runtime import (
    DUCKDB_MEMORY_LIMIT,
    DUCKDB_THREADS,
    MAX_CONCURRENT_QUERIES,
    QUERY_TIMEOUT_SECONDS,
)
from commercial_intelligence.products.taxonomy import family_codes
from commercial_intelligence.reporting import queries
from commercial_intelligence.reporting.queries import Filters, WarehouseUnavailableError

_CONNECTION_SLOTS = BoundedSemaphore(MAX_CONCURRENT_QUERIES)


def get_con() -> Iterator[duckdb.DuckDBPyConnection]:
    if not _CONNECTION_SLOTS.acquire(blocking=False):
        raise HTTPException(
            status_code=503,
            detail="The analytics service is busy. Please retry shortly.",
        )
    con: duckdb.DuckDBPyConnection | None = None
    timer: Timer | None = None
    try:
        con = queries.connect(threads=DUCKDB_THREADS, memory_limit=DUCKDB_MEMORY_LIMIT)
        # DuckDB's interrupt is thread-safe. The watchdog prevents an unexpectedly
        # expensive analytical request from occupying a worker indefinitely.
        timer = Timer(QUERY_TIMEOUT_SECONDS, con.interrupt)
        timer.daemon = True
        timer.start()
        yield con
    except WarehouseUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail="The analytical warehouse is unavailable. Run the documented pipeline.",
        ) from e
    finally:
        if timer is not None:
            timer.cancel()
        if con is not None:
            con.close()
        _CONNECTION_SLOTS.release()


def get_filters(
    start: date | None = Query(None, description="Inclusive start date (YYYY-MM-DD)."),
    end: date | None = Query(None, description="Inclusive end date (YYYY-MM-DD)."),
    market: str | None = Query(None, description="UK | International | Unknown."),
    family: str | None = Query(None, description="Product family code, e.g. KD."),
) -> Filters:
    if start and end and start > end:
        raise HTTPException(status_code=422, detail="start must be on or before end.")
    if market is not None and market not in queries.VALID_MARKETS:
        raise HTTPException(
            status_code=422,
            detail=f"market must be one of {list(queries.VALID_MARKETS)}.",
        )
    if family is not None and family not in family_codes():
        raise HTTPException(status_code=422, detail="family must be a known product-family code.")
    return Filters(start=start, end=end, market=market, family_code=family)


def applied(f: Filters) -> dict:
    return {"start": f.start, "end": f.end, "market": f.market, "family_code": f.family_code}
