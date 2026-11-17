"""FastAPI application entrypoint. Run: uvicorn api.main:app --reload"""

from __future__ import annotations

import logging

import duckdb
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from api.routers import (
    customers,
    executive,
    experiments,
    metadata,
    overview,
    pricing,
    products,
    revenue,
)
from api.runtime import CORS_ORIGINS

log = logging.getLogger(__name__)

app = FastAPI(
    title="Commercial Analytics & Pricing Strategy API",
    version="0.1.0",
    description=(
        "Read-only analytical endpoints. Interactive aggregates are parameterized "
        "warehouse queries; fixed-period analytics come from validated exports."
    ),
)

# Only explicit local frontend origins are allowed by default. A future deployment
# may set API_CORS_ORIGINS to a comma-separated list of exact HTTPS origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(CORS_ORIGINS),
    allow_methods=["GET"],
    allow_headers=["Accept", "Content-Type"],
    allow_credentials=False,
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "testserver"],
)


@app.exception_handler(duckdb.Error)
async def duckdb_error(_request: Request, exc: duckdb.Error) -> JSONResponse:
    log.exception("DuckDB reporting query failed", exc_info=exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "The analytical query could not be completed."},
    )


@app.exception_handler(Exception)
async def unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
    log.exception("Unhandled API error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal service error occurred."},
    )

app.include_router(metadata.router)
app.include_router(overview.router)
app.include_router(revenue.router)
app.include_router(products.router)
app.include_router(customers.router)
app.include_router(pricing.router)
app.include_router(experiments.router)
app.include_router(executive.router)


@app.get("/api/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}
