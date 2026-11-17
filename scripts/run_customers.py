"""M3 runner: segmentation, cohorts and CLV -> exports, plots and findings report.

Usage:
    python scripts/run_customers.py
Requires the warehouse (scripts/build_marts.py).
"""

from __future__ import annotations

import sys

import duckdb

from commercial_intelligence.common.config import load_settings, repo_path
from commercial_intelligence.customers.report import (
    render_report,
    run_analyses,
    write_exports,
    write_plots,
)


def main() -> int:
    settings = load_settings()
    warehouse = repo_path(settings["paths"]["warehouse"])
    if not warehouse.exists():
        print(f"Warehouse {warehouse} not found. Run scripts/build_marts.py.", file=sys.stderr)
        return 1

    paths = settings["customers"]["paths"]
    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        out = run_analyses(con)
        write_exports(out, repo_path(paths["export_dir"]))
        write_plots(out, repo_path(paths["assets_dir"]))
        report = render_report(out)
    finally:
        con.close()

    report_path = repo_path(paths["findings_report"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(f"Wrote {report_path}, exports to {repo_path(paths['export_dir'])} "
          f"and plots to {repo_path(paths['assets_dir'])}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
