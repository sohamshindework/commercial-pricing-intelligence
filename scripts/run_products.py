"""M4 runner: baseline vs LLM product classification -> exports + findings report.

Usage:
    python scripts/run_products.py
Requires the warehouse (scripts/build_marts.py) and the gold labels + LLM
predictions (committed under data/labels/ and tests/fixtures/).
"""

from __future__ import annotations

import sys

import duckdb

from commercial_intelligence.common.config import load_settings, repo_path
from commercial_intelligence.products.report import render_report, run, write_exports


def main() -> int:
    settings = load_settings()
    warehouse = repo_path(settings["paths"]["warehouse"])
    if not warehouse.exists():
        print(f"Warehouse {warehouse} not found. Run scripts/build_marts.py.", file=sys.stderr)
        return 1

    pcfg = settings["products"]
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
    print(
        f"Wrote {report_path}. Chosen method: {out.chosen}. "
        f"Held-out baseline macro-F1 {out.baseline_scores['macro_f1']:.3f}. "
        "Invalid LLM comparison withdrawn."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
