"""Pricing-opportunity list with revenue impact as RANGES under stated assumptions.

Every opportunity separates four things explicitly:
  * observation   — what the data shows (descriptive, measured);
  * hypothesis    — the commercial action being proposed;
  * scenario      — a revenue RANGE under stated capture assumptions (not a forecast);
  * validation    — that only the proposed experiment can establish a causal effect.
Margin is shown only as a labelled "assumed cost ratio" scenario; there is no
cost data.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import duckdb
import pandas as pd

from commercial_intelligence.pricing.dispersion import realization_gap


@dataclass
class Opportunity:
    key: str
    name: str
    observation: str
    hypothesis: str
    gap_gbp: float
    impact_low_gbp: float
    impact_high_gbp: float
    assumptions: list[str]
    confounders: list[str]
    margin_low_gbp: float = 0.0
    margin_high_gbp: float = 0.0
    detail: dict = field(default_factory=dict)


def _discount_leakage_gap(con: duckdb.DuckDBPyConnection, min_lines: int) -> float:
    """Price gap on small-quantity lines sold at a deep discount.

    "Small" means below the product's median line quantity, not a whole invoice.
    This approximates bulk-price leakage. Descriptive; excludes extreme lines.
    """
    (gap,) = con.execute(
        """
        with s as (
            select product_key,
                   quantile_cont(unit_price, 0.25) as p25,
                   median(unit_price)              as price_median,
                   median(quantity)                as qty_median,
                   count(*)                        as lines
            from fct_order_lines
            where line_type = 'sale' and not is_extreme_line
            group by product_key having count(*) >= ?
        )
        select coalesce(sum((s.price_median - f.unit_price) * f.quantity), 0)
        from fct_order_lines f join s using (product_key)
        where f.line_type = 'sale' and not f.is_extreme_line
          and f.unit_price < s.p25 and f.quantity < s.qty_median
        """,
        [min_lines],
    ).fetchone()
    return float(gap)


def build_opportunities(
    con: duckdb.DuckDBPyConnection, cfg: dict
) -> tuple[list[Opportunity], float]:
    min_lines = int(cfg["min_lines_for_dispersion"])
    lo, hi = float(cfg["capture_low"]), float(cfg["capture_high"])
    cost_ratio = float(cfg["assumed_cost_ratio"])
    (net_rev,) = con.execute(
        "select sum(line_amount) from fct_order_lines"
    ).fetchone()

    gaps = realization_gap(con, min_lines)
    realization_total = float(gaps["realization_gap_gbp"].sum())
    leakage_total = _discount_leakage_gap(con, min_lines)

    def margin(v: float) -> float:
        return v * (1 - cost_ratio)

    opps = [
        Opportunity(
            key="price_realization",
            name="Price realisation on high-dispersion products",
            observation=(
                f"{len(gaps):,} products (≥{min_lines} sale lines) are sold below their own "
                f"median unit price often enough to leave a measured price-realisation gap of "
                f"GBP {realization_total:,.0f} at unchanged volume."
            ),
            hypothesis=(
                "Tightening how far below the median list price these products can be sold "
                "(price-floor / discount governance) is associated with higher revenue."
            ),
            gap_gbp=realization_total,
            impact_low_gbp=realization_total * lo,
            impact_high_gbp=realization_total * hi,
            assumptions=[
                f"Only {int(lo*100)}–{int(hi*100)}% of the measured gap is recoverable "
                "(partial realisation).",
                "Volume is held constant — a strong assumption; higher prices may reduce units.",
                "Reference price = each product's own median; extreme-flagged lines excluded.",
            ],
            confounders=[
                "Below-median prices may reflect genuine quantity-break deals, clearance, or "
                "key-account pricing, not leakage.",
            ],
            margin_low_gbp=margin(realization_total * lo),
            margin_high_gbp=margin(realization_total * hi),
            detail={"products": int(len(gaps))},
        ),
        Opportunity(
            key="discount_leakage",
            name="Quantity-break redesign (discount leakage on small-quantity lines)",
            observation=(
                f"Small-quantity lines (below a product's median line quantity) are sometimes "
                f"sold at deep "
                f"discounts (below the product's 25th price percentile), a measured gap of "
                f"GBP {leakage_total:,.0f} versus the median price."
            ),
            hypothesis=(
                "Restricting deep discounts to genuinely large line quantities (a redesigned "
                "quantity-break schedule) is associated with higher revenue on small-quantity "
                "lines."
            ),
            gap_gbp=leakage_total,
            impact_low_gbp=leakage_total * lo,
            impact_high_gbp=leakage_total * hi,
            assumptions=[
                f"Only {int(lo*100)}–{int(hi*100)}% of the leakage gap is recoverable.",
                "Small-quantity discounted lines would still convert at the median price "
                "(uncertain).",
            ],
            confounders=[
                "Some small-quantity discounted lines are samples, staff sales or loyalty "
                "gestures.",
            ],
            margin_low_gbp=margin(leakage_total * lo),
            margin_high_gbp=margin(leakage_total * hi),
        ),
    ]
    return opps, float(net_rev)


def opportunities_frame(opps: list[Opportunity], net_rev: float) -> pd.DataFrame:
    rows = []
    for o in opps:
        rows.append({
            "key": o.key,
            "name": o.name,
            "measured_gap_gbp": round(o.gap_gbp, 0),
            "impact_low_gbp": round(o.impact_low_gbp, 0),
            "impact_high_gbp": round(o.impact_high_gbp, 0),
            "impact_low_pct_rev": round(100 * o.impact_low_gbp / net_rev, 2),
            "impact_high_pct_rev": round(100 * o.impact_high_gbp / net_rev, 2),
            "margin_scenario_low_gbp": round(o.margin_low_gbp, 0),
            "margin_scenario_high_gbp": round(o.margin_high_gbp, 0),
        })
    return pd.DataFrame(rows)
