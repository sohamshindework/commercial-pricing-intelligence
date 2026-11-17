"""Parameterized, read-only aggregate queries over the warehouse (for the API).

These power the *interactive* views (filter by date range, market, family). They
are presentation aggregates, not new business logic: the net-revenue definition
and the star schema live in the SQL marts (M1). The one shared definition —
net revenue = SUM(line_amount) over kept lines — is centralised in `NET_REVENUE`
and reused everywhere here so a filtered total always matches the marts.

Fixed-period analytics (CLV evaluation, classification metrics, revenue
decomposition) are NOT re-sliced here; those come from `reporting.exports`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import duckdb

from commercial_intelligence.common.config import load_settings, repo_path

# The single revenue definition, matching the marts and the DAX measures.
NET_REVENUE = "sum(f.line_amount)"
GROSS_REVENUE = "sum(f.line_amount) filter (where f.line_type = 'sale')"
CANCELLATIONS = "sum(f.line_amount) filter (where f.line_type = 'cancellation')"

VALID_MARKETS = ("UK", "International", "Unknown")


class WarehouseUnavailableError(RuntimeError):
    """The DuckDB warehouse has not been built yet (run scripts/build_marts.py)."""


@dataclass(frozen=True)
class Filters:
    start: date | None = None
    end: date | None = None
    market: str | None = None
    family_code: str | None = None


def connect(*, threads: int = 2, memory_limit: str = "512MB") -> duckdb.DuckDBPyConnection:
    """Read-only warehouse connection with a temp view joining product families."""
    if not 1 <= threads <= 8 or memory_limit not in {"256MB", "512MB", "1GB"}:
        raise ValueError("Invalid DuckDB resource limits.")
    settings = load_settings()
    wh = repo_path(settings["paths"]["warehouse"])
    if not wh.exists():
        raise WarehouseUnavailableError("The analytical warehouse has not been built.")
    con = duckdb.connect(str(wh), read_only=True)
    con.execute(f"set threads = {threads}")
    con.execute(f"set memory_limit = '{memory_limit}'")
    fam = repo_path(settings["pricing"]["product_families_path"])
    if fam.exists():
        # CREATE VIEW cannot take a bound parameter; the path is an internal
        # config value (not user input), so it is safe to inline via a literal.
        literal = str(fam).replace("'", "''")
        con.execute(
            "create temp table product_family as "
            f"select stock_code as product_key, family_code from read_parquet('{literal}')"
        )
    else:
        con.execute(
            "create temp table product_family as "
            "select product_key, cast(null as varchar) as family_code from dim_product"
        )
    # All required external data has now been materialised. Subsequent reporting
    # queries cannot read arbitrary files or load extensions.
    con.execute("set enable_external_access = false")
    return con


def _scope(f: Filters, extra_joins: tuple[str, ...] = ()) -> tuple[str, list]:
    """Build the FROM/JOIN/WHERE shared by every aggregate, with bound params."""
    joins = [
        "from fct_order_lines f",
        "left join dim_country c on c.country_key = f.country_key",
        "left join product_family pf on pf.product_key = f.product_key",
        *extra_joins,
    ]
    where, params = ["1 = 1"], []
    if f.start is not None:
        where.append("f.invoice_date >= ?")
        params.append(f.start)
    if f.end is not None:
        where.append("f.invoice_date <= ?")
        params.append(f.end)
    if f.market is not None:
        where.append("coalesce(c.market, 'Unknown') = ?")
        params.append(f.market)
    if f.family_code is not None:
        where.append("pf.family_code = ?")
        params.append(f.family_code)
    return " ".join(joins) + " where " + " and ".join(where), params


def date_bounds(con: duckdb.DuckDBPyConnection) -> tuple[date, date]:
    lo, hi = con.execute(
        "select min(invoice_date), max(invoice_date) from fct_order_lines"
    ).fetchone()
    return lo, hi


def markets(con: duckdb.DuckDBPyConnection) -> list[str]:
    rows = con.execute(
        "select distinct coalesce(market, 'Unknown') m from dim_country order by m"
    ).fetchall()
    return [r[0] for r in rows]


def families(con: duckdb.DuckDBPyConnection) -> list[dict]:
    rows = con.execute(
        "select distinct family_code from product_family "
        "where family_code is not null order by family_code"
    ).fetchall()
    return [{"family_code": r[0]} for r in rows]


def overview_kpis(con: duckdb.DuckDBPyConnection, f: Filters) -> dict:
    scope, params = _scope(f)
    row = con.execute(
        f"""
        select
            coalesce({NET_REVENUE}, 0)                                  as net_revenue,
            coalesce({GROSS_REVENUE}, 0)                                as gross_revenue,
            coalesce({CANCELLATIONS}, 0)                                as cancellations,
            count(distinct f.invoice_no) filter (where f.line_type = 'sale')
                                                                        as sale_invoices,
            count(distinct f.invoice_no) filter (where f.line_type = 'cancellation')
                                                                        as cancellation_invoices,
            count(distinct f.invoice_no)                                as all_invoices,
            count(distinct case when f.customer_key <> -1 then f.customer_key end)
                                                                        as active_customers,
            coalesce(sum(f.quantity) filter (where f.line_type = 'sale'), 0) as units_sold,
            coalesce(sum(f.line_amount) filter (where f.customer_key = -1), 0) as guest_revenue
        {scope}
        """,
        params,
    ).fetchone()
    net, gross, cancellations, sales, cancels, all_invoices, active, units, guest = row
    return {
        "net_revenue": float(net),
        "gross_revenue": float(gross),
        "cancellations": float(cancellations),
        "sale_invoices": int(sales),
        "cancellation_invoices": int(cancels),
        "all_invoices": int(all_invoices),
        "active_customers": int(active),
        "units_sold": int(units),
        "gross_sales_aov": float(gross) / sales if sales else 0.0,
        "guest_revenue_pct": (float(guest) / float(net) * 100) if net else 0.0,
    }


def revenue_trend(con: duckdb.DuckDBPyConnection, f: Filters) -> list[dict]:
    scope, params = _scope(f, ("join dim_date d on d.date_key = f.date_key",))
    rows = con.execute(
        f"""
        select d.year_month,
               coalesce({NET_REVENUE}, 0)            as net_revenue,
               count(distinct f.invoice_no) filter (where f.line_type='sale')
                                                       as sale_invoices,
               count(distinct f.invoice_no) filter (where f.line_type='cancellation')
                                                       as cancellation_invoices,
               bool_or(d.is_partial_month)           as is_partial_month
        {scope}
        group by d.year_month
        order by d.year_month
        """,
        params,
    ).fetchall()
    return [
        {"year_month": r[0], "net_revenue": float(r[1]), "sale_invoices": int(r[2]),
         "cancellation_invoices": int(r[3]), "is_partial_month": bool(r[4])}
        for r in rows
    ]


def revenue_by_market(con: duckdb.DuckDBPyConnection, f: Filters) -> list[dict]:
    scope, params = _scope(f)
    rows = con.execute(
        f"""
        select coalesce(c.market, 'Unknown') as market,
               coalesce({NET_REVENUE}, 0)    as net_revenue,
               count(distinct f.invoice_no) filter (where f.line_type='sale')
                                                as sale_invoices,
               count(distinct f.invoice_no) filter (where f.line_type='cancellation')
                                                as cancellation_invoices
        {scope}
        group by 1 order by net_revenue desc
        """,
        params,
    ).fetchall()
    return [
        {"market": r[0], "net_revenue": float(r[1]), "sale_invoices": int(r[2]),
         "cancellation_invoices": int(r[3])} for r in rows
    ]


def revenue_by_family(con: duckdb.DuckDBPyConnection, f: Filters) -> list[dict]:
    scope, params = _scope(f)
    rows = con.execute(
        f"""
        select coalesce(pf.family_code, 'NA') as family_code,
               coalesce({NET_REVENUE}, 0)     as net_revenue
        {scope}
        group by 1 order by net_revenue desc
        """,
        params,
    ).fetchall()
    return [{"family_code": r[0], "net_revenue": float(r[1])} for r in rows]


def top_products(
    con: duckdb.DuckDBPyConnection, f: Filters, limit: int, offset: int
) -> tuple[list[dict], int]:
    scope, params = _scope(f)
    total = con.execute(
        f"select count(distinct f.product_key) {scope}", params
    ).fetchone()[0]
    scope_p, _ = _scope(f, ("join dim_product p on p.product_key = f.product_key",))
    rows = con.execute(
        f"""
        select f.product_key, any_value(p.product_name) as product_name,
               coalesce(pf.family_code, 'NA')            as family_code,
               coalesce({NET_REVENUE}, 0)                as net_revenue,
               coalesce(sum(f.quantity) filter (where f.line_type='sale'), 0) as units
        {scope_p}
        group by f.product_key, pf.family_code
        order by net_revenue desc, f.product_key
        limit ? offset ?
        """,
        [*params, limit, offset],
    ).fetchall()
    items = [
        {"product_key": r[0], "product_name": r[1], "family_code": r[2],
         "net_revenue": float(r[3]), "units": int(r[4])}
        for r in rows
    ]
    return items, int(total)
