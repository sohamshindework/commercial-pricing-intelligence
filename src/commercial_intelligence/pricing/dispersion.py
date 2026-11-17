"""Price-dispersion analysis: the same product sold at different unit prices.

Uses a robust reference (the product's median unit price) so extreme outlier
lines (M1's F02 flag, excluded here) do not drive the numbers.
"""

from __future__ import annotations

import duckdb
import pandas as pd


def product_price_stats(con: duckdb.DuckDBPyConnection, min_lines: int) -> pd.DataFrame:
    """Per-product unit-price dispersion over sale lines (excluding extreme lines)."""
    return con.execute(
        """
        select
            p.product_key,
            pr.product_name,
            count(*)                                        as lines,
            count(distinct p.unit_price)                    as n_prices,
            min(p.unit_price)                               as price_min,
            max(p.unit_price)                               as price_max,
            median(p.unit_price)                            as price_median,
            quantile_cont(p.unit_price, 0.25)              as price_p25,
            quantile_cont(p.unit_price, 0.75)              as price_p75,
            sum(p.quantity)                                 as units,
            sum(p.line_amount)                              as revenue,
            stddev_samp(p.unit_price) / nullif(avg(p.unit_price), 0) as price_cv
        from fct_order_lines p
        join dim_product pr on pr.product_key = p.product_key
        where p.line_type = 'sale' and not p.is_extreme_line
        group by p.product_key, pr.product_name
        having count(*) >= ?
        """,
        [min_lines],
    ).df()


def dispersion_summary(stats: pd.DataFrame) -> dict[str, float]:
    multi = stats[stats["n_prices"] > 1]
    return {
        "products_analysed": int(len(stats)),
        "multi_price_products": int(len(multi)),
        "pct_multi_price": round(100 * len(multi) / max(len(stats), 1), 1),
        "median_price_cv": float(multi["price_cv"].median()) if len(multi) else 0.0,
    }


def realization_gap(con: duckdb.DuckDBPyConnection, min_lines: int) -> pd.DataFrame:
    """Per-product price-realisation gap.

    For sale lines priced BELOW the product's median unit price, the gap is
    Σ (median_price − unit_price) × quantity — the extra revenue that those
    transactions would have produced at the median price, assuming unchanged
    volume. This is a descriptive gap, the raw material for a scenario range,
    NOT a prediction (raising prices may reduce volume; only an experiment can
    tell). Extreme-flagged lines are excluded.
    """
    return con.execute(
        """
        with med as (
            select product_key, median(unit_price) as price_median, count(*) as lines
            from fct_order_lines
            where line_type = 'sale' and not is_extreme_line
            group by product_key
            having count(*) >= ?
        ),
        lines as (
            select
                f.product_key,
                m.price_median,
                f.quantity,
                f.unit_price,
                case when f.unit_price < m.price_median
                     then (m.price_median - f.unit_price) * f.quantity else 0 end as gap
            from fct_order_lines f
            join med m on m.product_key = f.product_key
            where f.line_type = 'sale' and not f.is_extreme_line
        )
        select
            product_key,
            any_value(price_median)                         as price_median,
            sum(gap)                                         as realization_gap_gbp,
            sum(quantity) filter (where unit_price < price_median) as below_median_units,
            sum(unit_price * quantity) filter (where unit_price < price_median)
                                                            as below_median_revenue
        from lines
        group by product_key
        having sum(gap) > 0
        order by realization_gap_gbp desc
        """,
        [min_lines],
    ).df()
