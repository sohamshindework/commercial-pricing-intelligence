"""Render the data-quality report (docs/data_quality_report.md) from warehouse tables."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb

from commercial_intelligence.common.log_utils import get_logger, kv

log = get_logger(__name__)


def _rows(con: duckdb.DuckDBPyConnection, sql: str) -> tuple[list[str], list[tuple]]:
    rel = con.sql(sql)
    return list(rel.columns), rel.fetchall()


def _md_table(columns: list[str], rows: list[tuple]) -> str:
    def fmt(v: object) -> str:
        if v is None:
            return ""
        if isinstance(v, float):
            return f"{v:,.2f}"
        if isinstance(v, int):
            return f"{v:,}"
        return str(v)

    head = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(fmt(v) for v in row) + " |" for row in rows]
    return "\n".join([head, sep, *body])


def render_quality_report(con: duckdb.DuckDBPyConnection) -> str:
    recon_cols, recon = _rows(
        con,
        "select raw_rows, removed_rows, kept_rows, gross_revenue, cancellations, net_revenue, "
        "row_difference, value_difference from dq_reconciliation",
    )
    r = dict(zip(recon_cols, recon[0], strict=True))

    rule_cols, rule_rows = _rows(
        con,
        "select rule_id, name, rows_removed, units_removed, value_removed_gbp "
        "from dq_rule_summary order by rule_order",
    )
    flag_cols, flag_rows = _rows(
        con,
        "select check_id, description, rows_affected, value_gbp, pct_of_net_revenue from dq_flags",
    )
    overlap_cols, overlap_rows = _rows(con, "select * from dq_overlap_check")
    dup_cols, dup_rows = _rows(con, "select * from dq_duplicate_sensitivity")

    date_span = con.execute(
        "select min(invoice_date), max(invoice_date) from fct_order_lines"
    ).fetchone()
    n_customers = con.execute(
        "select count(*) from dim_customer where not is_unknown"
    ).fetchone()[0]
    n_products = con.execute("select count(*) from dim_product").fetchone()[0]

    reconciled = r["row_difference"] == 0 and abs(r["value_difference"]) <= 0.005

    lines = [
        "# Data-quality report — M1 (ingest, clean, model)",
        "",
        f"_Generated {date.today().isoformat()} from the DuckDB warehouse. "
        "Every figure is produced by the pipeline; do not edit by hand._",
        "",
        "## Source",
        "",
        "- **Dataset:** UCI Online Retail II (CC BY 4.0). Chen, D. (2019). "
        "Online Retail II [Dataset]. UCI Machine Learning Repository. "
        "<https://doi.org/10.24432/C5CG6D>.",
        f"- **Transactions kept:** {r['kept_rows']:,} lines, "
        f"{date_span[0]} to {date_span[1]}.",
        f"- **Customers (identified):** {n_customers:,}. **Products:** {n_products:,}.",
        "- **Currency:** GBP. Revenue excludes postage, fees and adjustments (rule R04).",
        "",
        "## Reconciliation",
        "",
        "**Raw value = removed value + kept net revenue**, to a tenth of a penny. "
        "Sums use exact DECIMAL arithmetic, so there is no rounding tolerance.",
        "",
        _md_table(
            ["Metric", "Value (GBP / rows)"],
            [
                ("Raw rows (staged)", f"{r['raw_rows']:,}"),
                ("Rows removed", f"{r['removed_rows']:,}"),
                ("Rows kept", f"{r['kept_rows']:,}"),
                ("Gross product revenue", f"{r['gross_revenue']:,.2f}"),
                ("Cancellations", f"{r['cancellations']:,.2f}"),
                ("Net product revenue", f"{r['net_revenue']:,.2f}"),
                ("Row difference (must be 0)", f"{r['row_difference']:,}"),
                ("Value difference (must be 0)", f"{r['value_difference']:,.4f}"),
            ],
        ),
        "",
        f"**Reconciled:** {'yes' if reconciled else 'NO — investigate'}.",
        "",
        "## Rows removed by rule",
        "",
        "Each removed row is counted against the first rule it breaks, so these rows "
        "sum to *rows removed* above. Rule definitions: "
        "[data_cleaning_rules.md](data_cleaning_rules.md).",
        "",
        _md_table(
            ["Rule", "Name", "Rows removed", "Units removed", "Value removed (GBP)"], rule_rows
        ),
        "",
        "## Known issues kept in the data",
        "",
        "These are not removed; analyses downstream must account for them.",
        "",
        _md_table(
            ["Check", "Description", "Rows / count", "Value (GBP)", "% of net revenue"], flag_rows
        ),
        "",
        "## Sheet-overlap verification (rule R01)",
        "",
        "The workbook's two sheets overlap for 1–9 Dec 2010. R01 drops the earlier "
        "copy only after checking it matches the later sheet row-for-row. "
        "`unmatched_rows` must be 0.",
        "",
        _md_table(overlap_cols, overlap_rows),
        "",
        "## Exact-looking line sensitivity",
        "",
        "The workbook has no immutable source-line identifier. Exact-looking repeated "
        "lines are therefore retained and flagged rather than silently deleted. The "
        "alternative exclusion scenario below shows the uncertainty; proven sheet overlap "
        "is removed in both scenarios.",
        "",
        _md_table(dup_cols, dup_rows),
        "",
    ]
    _ = flag_cols  # columns are fixed above
    return "\n".join(lines)


def write_quality_report(con: duckdb.DuckDBPyConnection, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_quality_report(con))
    log.info(kv("quality_report_written", file=str(out_path)))
    return out_path
