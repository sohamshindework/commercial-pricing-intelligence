"""Export the star schema and a measure-reconciliation table for Power BI.

Writes fact + dimension tables (Parquet + CSV) that the TMDL semantic model and
the dashboard are built on, plus `measures_reconciliation.csv` — the KPI values
computed in Python that the DAX measures must reproduce (the README reconciliation
table draws from this).
"""

from __future__ import annotations

import sys

import duckdb
import pandas as pd

from commercial_intelligence.common.config import load_settings, repo_path
from commercial_intelligence.common.log_utils import get_logger, kv

log = get_logger(__name__)

STAR_TABLES = ("fct_order_lines", "dim_customer", "dim_date", "dim_country")


def _dim_product_with_family(con: duckdb.DuckDBPyConnection, families_path) -> pd.DataFrame:
    from commercial_intelligence.products.taxonomy import code_to_name

    dim = con.execute("select * from dim_product").df()
    if families_path.exists():
        fam = pd.read_parquet(families_path)[["stock_code", "family_code"]]
        dim = dim.merge(
            fam.rename(columns={"stock_code": "product_key"}), on="product_key", how="left"
        )
        dim["family_code"] = dim["family_code"].fillna("NA")
        dim["family"] = dim["family_code"].map(code_to_name()).fillna("Unclassified")
    else:
        dim["family_code"] = "NA"
        dim["family"] = "Unclassified"
    return dim


def _reconciliation(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    rows = con.execute(
        """
        select
            sum(line_amount)                                           as net_revenue,
            sum(line_amount) filter (where line_type='sale')           as gross_revenue,
            coalesce(sum(line_amount) filter (where line_type='cancellation'), 0)
                                                                        as cancellations,
            count(distinct invoice_no) filter (where line_type='sale') as sale_invoices,
            count(distinct invoice_no) filter (where line_type='cancellation')
                                                                        as cancellation_invoices,
            count(distinct invoice_no)                                 as all_invoices,
            (sum(line_amount) filter (where line_type='sale'))
              / nullif(count(distinct invoice_no) filter (where line_type='sale'), 0)
                                                                        as gross_sales_aov,
            count(distinct case when customer_key<>-1 then customer_key end) as active_customers,
            sum(quantity) filter (where line_type='sale')              as units_sold,
            count(*)                                                   as fact_rows
        from fct_order_lines
        """
    ).df()
    long = rows.T.reset_index()
    long.columns = ["measure", "python_value"]
    long["dax_measure"] = [
        "[Net Revenue]", "[Gross Revenue]", "[Cancellations]", "[Sale Invoices]",
        "[Cancellation Invoices]", "[All Invoices]", "[Gross Sales AOV]",
        "[Active Customers]", "[Units Sold]", "[Fact Row Count]",
    ]
    return long[["measure", "dax_measure", "python_value"]]


def main() -> int:
    settings = load_settings()
    warehouse = repo_path(settings["paths"]["warehouse"])
    if not warehouse.exists():
        print(f"Warehouse {warehouse} not found. Run scripts/build_marts.py.", file=sys.stderr)
        return 1

    out_dir = repo_path(settings["powerbi"]["export_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    families_path = repo_path(settings["pricing"]["product_families_path"])

    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        for t in STAR_TABLES:
            df = con.execute(f"select * from {t}").df()
            df.to_parquet(out_dir / f"{t}.parquet", index=False)
            df.to_csv(out_dir / f"{t}.csv", index=False)
        dim_product = _dim_product_with_family(con, families_path)
        dim_product.to_parquet(out_dir / "dim_product.parquet", index=False)
        dim_product.to_csv(out_dir / "dim_product.csv", index=False)

        # Convenience aggregates for the app (revenue needs the fact table).
        con.register("dim_product_fam", dim_product[["product_key", "family_code", "family"]])
        rev_fam = con.execute(
            """
            select coalesce(d.family, 'Unclassified') as family,
                   sum(f.line_amount) as net_revenue,
                   sum(f.quantity) filter (where f.line_type='sale') as units,
                   count(distinct f.invoice_no) filter (where f.line_type='sale')
                       as sale_invoices,
                   count(distinct f.invoice_no) filter (where f.line_type='cancellation')
                       as cancellation_invoices
            from fct_order_lines f
            left join dim_product_fam d on d.product_key = f.product_key
            group by 1 order by net_revenue desc
            """
        ).df()
        top_products = con.execute(
            """
            select f.product_key, p.product_name, coalesce(d.family,'Unclassified') as family,
                   sum(f.line_amount) as net_revenue,
                   sum(f.quantity) filter (where f.line_type='sale') as units
            from fct_order_lines f
            join dim_product p on p.product_key = f.product_key
            left join dim_product_fam d on d.product_key = f.product_key
            group by 1,2,3 order by net_revenue desc limit 50
            """
        ).df()
        for name, df in (("revenue_by_family", rev_fam), ("top_products", top_products)):
            df.to_parquet(out_dir / f"{name}.parquet", index=False)
            df.to_csv(out_dir / f"{name}.csv", index=False)

        duplicate_sensitivity = con.execute(
            "select * from dq_duplicate_sensitivity order by duplicate_policy"
        ).df()
        duplicate_sensitivity.to_parquet(
            out_dir / "duplicate_sensitivity.parquet", index=False
        )
        duplicate_sensitivity.to_csv(out_dir / "duplicate_sensitivity.csv", index=False)

        recon = _reconciliation(con)
        recon.to_csv(out_dir / "measures_reconciliation.csv", index=False)
        recon.to_parquet(out_dir / "measures_reconciliation.parquet", index=False)
    finally:
        con.close()

    log.info(kv("powerbi_export_done", dir=str(out_dir), tables=len(STAR_TABLES) + 1))
    print(f"Exported star schema + reconciliation to {out_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
