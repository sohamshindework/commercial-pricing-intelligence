"""M2 runner: build revenue bridges, write exports and the findings report.

Usage:
    python scripts/run_revenue.py
Requires the warehouse (scripts/build_marts.py) to exist.
"""

from __future__ import annotations

import sys

import duckdb

from commercial_intelligence.common.config import load_settings, repo_path
from commercial_intelligence.revenue.report import (
    build_all,
    comparisons_from_settings,
    render_report,
    write_exports,
)


def main() -> int:
    settings = load_settings()
    warehouse = repo_path(settings["paths"]["warehouse"])
    if not warehouse.exists():
        print(f"Warehouse {warehouse} not found. Run scripts/build_marts.py.", file=sys.stderr)
        return 1

    rev_paths = settings["revenue"]["paths"]
    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        comparisons = comparisons_from_settings()
        data = build_all(con, comparisons)
        write_exports(data, repo_path(rev_paths["export_dir"]))
        report = render_report(con, data)
    finally:
        con.close()

    out = repo_path(rev_paths["findings_report"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)
    print(f"Wrote {out} and exports to {repo_path(rev_paths['export_dir'])}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
