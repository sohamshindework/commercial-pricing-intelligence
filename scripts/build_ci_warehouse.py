"""Build the ignored DuckDB warehouse from the committed sample fixture for CI.

This is deliberately separate from the production download path: CI validates the
same SQL pipeline without downloading or committing the full source dataset.
"""

from __future__ import annotations

import os

from commercial_intelligence.common.config import load_settings, repo_path
from commercial_intelligence.ingestion.pipeline import run_pipeline


def main() -> int:
    if os.getenv("CI", "").lower() != "true":
        raise RuntimeError("build_ci_warehouse.py may run only with CI=true")
    settings = load_settings()
    fixture = repo_path(settings["paths"]["fixture_parquet"])
    warehouse = repo_path(settings["paths"]["warehouse"])
    if not fixture.exists():
        raise FileNotFoundError("The committed CI fixture is missing.")
    if warehouse.exists():
        raise FileExistsError("Refusing to overwrite an existing warehouse.")
    result = run_pipeline(fixture, warehouse)
    print(
        f"Built CI warehouse from committed fixture: {result.kept_rows:,} rows; "
        f"GBP {result.net_revenue:,.2f} net revenue."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
