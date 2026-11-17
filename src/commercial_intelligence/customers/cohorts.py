"""Monthly cohort retention.

A customer's cohort is the month of their first sale. Retention at month-offset k
is the share of the cohort that made at least one sale in the k-th month after
acquisition (offset 0 = acquisition month, always 100%). Guests are excluded.
Returns (cancellations) do not count as activity.
"""

from __future__ import annotations

import duckdb
import pandas as pd


def cohort_activity(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Long form: one row per (cohort_month, month_offset) with active customer count."""
    return con.execute(
        """
        with firsts as (
            select customer_key, date_trunc('month', min(invoice_date)) as cohort_month
            from fct_order_lines
            where customer_key <> -1 and line_type = 'sale'
            group by customer_key
        ),
        activity as (
            select distinct f.customer_key,
                   date_trunc('month', f.invoice_date) as active_month
            from fct_order_lines f
            where f.customer_key <> -1 and f.line_type = 'sale'
        )
        select
            fi.cohort_month,
            date_diff('month', fi.cohort_month, a.active_month) as month_offset,
            count(distinct a.customer_key)                      as active_customers
        from activity a
        join firsts fi using (customer_key)
        group by fi.cohort_month, month_offset
        order by fi.cohort_month, month_offset
        """
    ).df()


def retention_matrix(con: duckdb.DuckDBPyConnection) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (counts, rates) matrices: index=cohort_month, columns=month_offset."""
    long = cohort_activity(con)
    counts = long.pivot(index="cohort_month", columns="month_offset", values="active_customers")
    cohort_size = counts[0]
    rates = counts.div(cohort_size, axis=0)
    counts = counts.assign(cohort_size=cohort_size)
    return counts, rates


def retention_curve(rates: pd.DataFrame, max_offset: int = 12) -> pd.DataFrame:
    """Average retention by month-offset across cohorts old enough to be observed.

    Only cohorts with at least `offset` months of observation contribute to each
    offset, so the curve is not biased upward by young cohorts.
    """
    offsets = [o for o in rates.columns if isinstance(o, int) and 0 <= o <= max_offset]
    rows = []
    for o in offsets:
        col = rates[o].dropna()
        rows.append(
            {"month_offset": o, "avg_retention": float(col.mean()), "cohorts": int(col.size)}
        )
    return pd.DataFrame(rows)
