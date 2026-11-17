"""Build the DuckDB warehouse from the landing Parquet and write the quality report.

Usage:
    python scripts/build_marts.py
Run scripts/download.py first to create the landing Parquet file.
"""

from __future__ import annotations

import sys

import duckdb

from commercial_intelligence.common.config import load_settings, repo_path
from commercial_intelligence.ingestion.pipeline import run_pipeline
from commercial_intelligence.validation.quality_report import write_quality_report


def main() -> int:
    settings = load_settings()
    paths = settings["paths"]
    landing = repo_path(paths["landing_parquet"])
    if not landing.exists():
        print(f"Landing file {landing} not found. Run: python scripts/download.py", file=sys.stderr)
        return 1

    warehouse = repo_path(paths["warehouse"])
    result = run_pipeline(landing, warehouse)

    con = duckdb.connect(str(warehouse))
    try:
        write_quality_report(con, repo_path(paths["quality_report"]))
    finally:
        con.close()

    print(
        f"Built {warehouse}: {result.kept_rows:,} kept lines, "
        f"net revenue GBP {result.net_revenue:,.2f}. Reconciled."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
