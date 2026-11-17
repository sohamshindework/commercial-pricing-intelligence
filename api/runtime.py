"""Conservative runtime limits for the local read-only analytics API."""

from __future__ import annotations

import os
from urllib.parse import urlsplit


def _bounded_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{name} must be between {minimum} and {maximum}.")
    return value


def _bounded_float(name: str, default: float, *, minimum: float, maximum: float) -> float:
    raw = os.getenv(name, str(default))
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be numeric.") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{name} must be between {minimum} and {maximum}.")
    return value


def _origins() -> tuple[str, ...]:
    raw = os.getenv(
        "API_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    origins = tuple(origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip())
    for origin in origins:
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.path
            or parsed.query
            or parsed.fragment
            or "*" in origin
        ):
            raise RuntimeError("API_CORS_ORIGINS must contain explicit HTTP(S) origins.")
    return origins


MAX_CONCURRENT_QUERIES = _bounded_int(
    "API_MAX_CONCURRENT_QUERIES", 4, minimum=1, maximum=16
)
QUERY_TIMEOUT_SECONDS = _bounded_float(
    "API_QUERY_TIMEOUT_SECONDS", 10.0, minimum=0.1, maximum=60.0
)
DUCKDB_THREADS = _bounded_int("API_DUCKDB_THREADS", 2, minimum=1, maximum=8)
DUCKDB_MEMORY_LIMIT = "512MB"
CORS_ORIGINS = _origins()
