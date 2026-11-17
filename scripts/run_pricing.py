"""M5 runner: pricing opportunities + experiment design -> exports, workbook, report.

Usage:
    python scripts/run_pricing.py
Requires the warehouse (scripts/build_marts.py) and M4's product families
(scripts/run_products.py).
"""

from __future__ import annotations

import sys

import duckdb

from commercial_intelligence.common.config import load_settings, repo_path
from commercial_intelligence.pricing.report import render_report, run, write_exports


def main() -> int:
    settings = load_settings()
    warehouse = repo_path(settings["paths"]["warehouse"])
    families = repo_path(settings["pricing"]["product_families_path"])
    if not warehouse.exists():
        print(f"Warehouse {warehouse} not found. Run scripts/build_marts.py.", file=sys.stderr)
        return 1
    if not families.exists():
        print(f"Product families {families} not found. Run scripts/run_products.py.",
              file=sys.stderr)
        return 1

    pcfg = settings["pricing"]
    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        out = run(con)
        write_exports(out, repo_path(pcfg["export_dir"]))
        report = render_report(out)
    finally:
        con.close()

    report_path = repo_path(pcfg["findings_report"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(f"Wrote {report_path} and {out.workbook_path}. "
          f"Power: {out.power_result.n_per_group} independent SKUs/arm required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
