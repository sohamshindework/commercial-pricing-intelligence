"""DuckDB pipeline runner: landing Parquet -> staging -> intermediate -> marts -> quality.

The runner is deliberately thin. All logic lives in the ordered SQL files under
sql/; this module loads seeds, sets config variables, executes each file and runs
the reconciliation checks that make M1 "done".
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb

from commercial_intelligence.common.config import SQL_DIR, load_settings, repo_path
from commercial_intelligence.common.log_utils import get_logger, kv

log = get_logger(__name__)

# SQL files run in this order. Each builds one table named after the file.
SQL_STEPS: tuple[tuple[str, str], ...] = (
    ("staging", "stg_transactions"),
    ("intermediate", "int_transactions_flagged"),
    ("intermediate", "int_order_lines"),
    ("marts", "dim_country"),
    ("marts", "dim_product"),
    ("marts", "dim_customer"),
    ("marts", "dim_date"),
    ("marts", "fct_order_lines"),
    ("quality", "dq_overlap_check"),
    ("quality", "dq_rule_summary"),
    ("quality", "dq_duplicate_sensitivity"),
    ("quality", "dq_reconciliation"),
    ("quality", "dq_flags"),
)

SEEDS: tuple[tuple[str, str], ...] = (
    ("seed_non_product_codes", "sql/seeds/non_product_codes.csv"),
    ("seed_country_region", "sql/seeds/country_region.csv"),
    ("seed_cleaning_rules", "sql/seeds/cleaning_rules.csv"),
)


class ReconciliationError(RuntimeError):
    """Raised when cleaned totals do not reconcile to raw totals."""


@dataclass
class PipelineResult:
    raw_rows: int
    kept_rows: int
    removed_rows: int
    gross_revenue: float
    cancellations: float
    net_revenue: float
    row_difference: int
    value_difference: float
    overlap_unmatched: int


def _sql_text(layer: str, name: str) -> str:
    return (SQL_DIR / layer / f"{name}.sql").read_text()


def load_seeds(con: duckdb.DuckDBPyConnection) -> None:
    for table, rel_path in SEEDS:
        path = repo_path(rel_path)
        con.execute(
            f"create or replace table {table} as "
            "select * from read_csv(?, header=true, all_varchar=false)",
            [str(path)],
        )
        log.info(kv("seed_loaded", table=table))


def set_config_variables(con: duckdb.DuckDBPyConnection, settings: dict) -> None:
    cleaning = settings["cleaning"]
    con.execute("set variable extreme_quantity = ?", [int(cleaning["extreme_quantity"])])
    con.execute(
        "set variable extreme_line_value_gbp = ?", [int(cleaning["extreme_line_value_gbp"])]
    )


def run_pipeline(
    landing_parquet: Path,
    warehouse_path: Path | None = None,
    *,
    check: bool = True,
) -> PipelineResult:
    """Build every table from the landing Parquet file.

    If warehouse_path is given the warehouse is persisted there; otherwise the
    pipeline runs in memory (used by tests on the fixture).
    """
    settings = load_settings()
    if warehouse_path is not None:
        warehouse_path.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(warehouse_path))
    else:
        con = duckdb.connect()

    try:
        con.execute(
            "create or replace table raw_transactions as select * from read_parquet(?)",
            [str(landing_parquet)],
        )
        raw_rows = con.execute("select count(*) from raw_transactions").fetchone()[0]
        log.info(kv("raw_loaded", rows=raw_rows, file=landing_parquet.name))

        load_seeds(con)
        set_config_variables(con, settings)

        for layer, name in SQL_STEPS:
            con.execute(_sql_text(layer, name))
            rows = con.execute(f"select count(*) from {name}").fetchone()[0]
            log.info(kv("step_done", table=name, rows=rows))

        recon = con.execute(
            "select raw_rows, removed_rows, kept_rows, gross_revenue, cancellations, "
            "net_revenue, row_difference, value_difference from dq_reconciliation"
        ).fetchone()
        overlap_unmatched = con.execute(
            "select unmatched_rows from dq_overlap_check"
        ).fetchone()[0]

        result = PipelineResult(
            raw_rows=int(recon[0]),
            removed_rows=int(recon[1]),
            kept_rows=int(recon[2]),
            gross_revenue=float(recon[3]),
            cancellations=float(recon[4]),
            net_revenue=float(recon[5]),
            row_difference=int(recon[6]),
            value_difference=float(recon[7]),
            overlap_unmatched=int(overlap_unmatched),
        )

        if check:
            _assert_reconciled(result)
        log.info(
            kv(
                "pipeline_done",
                raw_rows=result.raw_rows,
                kept_rows=result.kept_rows,
                net_revenue=round(result.net_revenue, 2),
            )
        )
        return result
    finally:
        con.close()


def _assert_reconciled(result: PipelineResult) -> None:
    problems = []
    if result.row_difference != 0:
        problems.append(f"row_difference={result.row_difference}")
    if abs(result.value_difference) > 0.005:
        problems.append(f"value_difference={result.value_difference}")
    if result.overlap_unmatched != 0:
        problems.append(f"overlap_unmatched={result.overlap_unmatched}")
    if problems:
        raise ReconciliationError("; ".join(problems))
