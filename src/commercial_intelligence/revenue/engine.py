"""Feed the warehouse into the decomposition functions and build tidy bridge tables.

The arithmetic lives in decomposition.py; this module only pulls per-period
aggregates from fct_order_lines and shapes the results for a waterfall chart,
the memo, Power BI and the web app (via FastAPI). One implementation, many consumers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import duckdb
import pandas as pd

from commercial_intelligence.common.log_utils import get_logger
from commercial_intelligence.revenue.decomposition import (
    CustomerBridge,
    PVMBridge,
    customer_bridge,
    geography_bridge,
    pvm_bridge,
)

log = get_logger(__name__)


@dataclass(frozen=True)
class Period:
    label: str
    start: date
    end: date


@dataclass(frozen=True)
class Comparison:
    name: str
    label: str
    base: Period
    current: Period


# ---- aggregate pulls -------------------------------------------------------

def _product_gross(con: duckdb.DuckDBPyConnection, p: Period) -> dict[str, tuple[float, float]]:
    rows = con.execute(
        "select product_key, sum(quantity), sum(line_amount) "
        "from fct_order_lines "
        "where line_type = 'sale' and invoice_date between ? and ? "
        "group by product_key",
        [p.start, p.end],
    ).fetchall()
    return {r[0]: (float(r[1]), float(r[2])) for r in rows}


def _cancellations(con: duckdb.DuckDBPyConnection, p: Period) -> float:
    (v,) = con.execute(
        "select coalesce(sum(line_amount), 0) from fct_order_lines "
        "where line_type = 'cancellation' and invoice_date between ? and ?",
        [p.start, p.end],
    ).fetchone()
    return float(v)


def _customer_net(con: duckdb.DuckDBPyConnection, p: Period) -> dict[object, float]:
    rows = con.execute(
        "select customer_key, sum(line_amount) from fct_order_lines "
        "where invoice_date between ? and ? group by customer_key",
        [p.start, p.end],
    ).fetchall()
    return {r[0]: float(r[1]) for r in rows}


def _market_net(con: duckdb.DuckDBPyConnection, p: Period) -> dict[str, float]:
    rows = con.execute(
        "select coalesce(c.market, 'Unknown'), sum(f.line_amount) "
        "from fct_order_lines f left join dim_country c on f.country_key = c.country_key "
        "where f.invoice_date between ? and ? group by 1",
        [p.start, p.end],
    ).fetchall()
    return {r[0]: float(r[1]) for r in rows}


def _net_revenue(con: duckdb.DuckDBPyConnection, p: Period) -> float:
    (v,) = con.execute(
        "select coalesce(sum(line_amount), 0) from fct_order_lines "
        "where invoice_date between ? and ?",
        [p.start, p.end],
    ).fetchone()
    return float(v)


# ---- bridge builders -------------------------------------------------------

def build_product_bridge(
    con: duckdb.DuckDBPyConnection, cmp: Comparison
) -> tuple[PVMBridge, float, float]:
    base = _product_gross(con, cmp.base)
    current = _product_gross(con, cmp.current)
    bridge = pvm_bridge(base, current)
    cancel_base = _cancellations(con, cmp.base)
    cancel_current = _cancellations(con, cmp.current)
    return bridge, cancel_base, cancel_current


def product_bridge_frame(
    bridge: PVMBridge, cancel_base: float, cancel_current: float, cmp: Comparison
) -> pd.DataFrame:
    """Tidy waterfall rows: start -> price/volume/mix/new/disc/returns -> end (net)."""
    cancel_change = cancel_current - cancel_base
    base_net = bridge.base_gross + cancel_base
    current_net = bridge.current_gross + cancel_current
    steps = [
        ("Base net revenue", base_net, "start"),
        ("Price", bridge.price, "delta"),
        ("Volume", bridge.volume, "delta"),
        ("Mix", bridge.mix, "delta"),
        ("New products", bridge.new_products, "delta"),
        ("Discontinued products", -bridge.discontinued_products, "delta"),
        ("Returns (cancellations)", cancel_change, "delta"),
        ("Unexplained residual", bridge.residual, "delta"),
        ("Current net revenue", current_net, "end"),
    ]
    return _to_frame("product", cmp, steps)


def build_customer_bridge(con: duckdb.DuckDBPyConnection, cmp: Comparison) -> CustomerBridge:
    return customer_bridge(_customer_net(con, cmp.base), _customer_net(con, cmp.current))


def customer_bridge_frame(bridge: CustomerBridge, cmp: Comparison) -> pd.DataFrame:
    steps = [
        ("Base net revenue", bridge.base_net, "start"),
        ("New customers", bridge.new_customers, "delta"),
        ("Lost customers", -bridge.lost_customers, "delta"),
        ("Retained customers", bridge.retained_customers, "delta"),
        ("Guest / unidentified", bridge.guest, "delta"),
        ("Residual", bridge.residual, "delta"),
        ("Current net revenue", bridge.current_net, "end"),
    ]
    return _to_frame("customer", cmp, steps)


def geography_bridge_frame(con: duckdb.DuckDBPyConnection, cmp: Comparison) -> pd.DataFrame:
    base = _market_net(con, cmp.base)
    current = _market_net(con, cmp.current)
    changes = geography_bridge(base, current)
    base_net = sum(base.values())
    current_net = sum(current.values())
    order = ["UK", "International", "Unknown"]
    ordered = sorted(changes, key=lambda m: (order.index(m) if m in order else 99, m))
    steps = [("Base net revenue", base_net, "start")]
    steps += [(m, changes[m], "delta") for m in ordered]
    steps.append(("Current net revenue", current_net, "end"))
    return _to_frame("geography", cmp, steps)


def _to_frame(lens: str, cmp: Comparison, steps: list[tuple[str, float, str]]) -> pd.DataFrame:
    # Publish all bridge values at penny precision and make that published view
    # reconcile in integer pennies. Computing the analytical residual before
    # rounding can otherwise leave a one-penny display gap even when the
    # unrounded decomposition closes.
    rounded = [(name, int(round(value * 100)), kind) for name, value, kind in steps]
    start_cents = next(value for _, value, kind in rounded if kind == "start")
    end_cents = next(value for _, value, kind in rounded if kind == "end")
    delta_cents = sum(value for _, value, kind in rounded if kind == "delta")
    adjustment = end_cents - start_cents - delta_cents
    if adjustment:
        residual_index = next(
            (i for i, (name, _, kind) in enumerate(rounded)
             if kind == "delta" and "residual" in name.lower()),
            None,
        )
        if residual_index is None:
            rounded.insert(-1, ("Rounding residual", adjustment, "delta"))
        else:
            name, value, kind = rounded[residual_index]
            rounded[residual_index] = (name, value + adjustment, kind)

    return pd.DataFrame(
        {
            "lens": lens,
            "comparison": cmp.name,
            "comparison_label": cmp.label,
            "step_order": range(len(rounded)),
            "component": [s[0] for s in rounded],
            "value_gbp": [s[1] / 100 if s[1] else 0.0 for s in rounded],
            "kind": [s[2] for s in rounded],
        }
    )


def monthly_series(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute(
        """
        select
            d.year_month,
            d.is_partial_month,
            count(*)                                                        as lines,
            sum(f.line_amount) filter (where f.line_type = 'sale')         as gross_revenue,
            coalesce(sum(f.line_amount) filter (where f.line_type = 'cancellation'), 0)
                                                                           as cancellations,
            sum(f.line_amount)                                             as net_revenue,
            count(distinct f.invoice_no) filter (where f.line_type = 'sale')
                                                                           as sale_invoices,
            count(distinct f.invoice_no) filter (where f.line_type = 'cancellation')
                                                                           as cancellation_invoices,
            count(distinct case when f.customer_key <> -1 then f.customer_key end)
                                                                           as active_customers
        from fct_order_lines f
        join dim_date d on f.date_key = d.date_key
        group by d.year_month, d.is_partial_month
        order by d.year_month
        """
    ).df()
