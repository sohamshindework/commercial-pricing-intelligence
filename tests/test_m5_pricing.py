"""M5: dispersion/opportunity SQL, price-response OLS, workbook, no-causal guard."""

from __future__ import annotations

import duckdb
import numpy as np
import pytest

from commercial_intelligence.pricing import dispersion, price_response
from commercial_intelligence.pricing.experiment import PowerResult, design_price_experiment
from commercial_intelligence.pricing.opportunities import Opportunity, opportunities_frame
from commercial_intelligence.pricing.report import _assert_no_causal_elasticity
from commercial_intelligence.pricing.workbook import write_sizing_workbook


def _synthetic_con() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    # One product sold at 8, 10, 12 (median 10); below-median lines: price 8 x qty 5.
    con.execute(
        """
        create table fct_order_lines as
        select * from (values
            ('P1','sale', 8.0, 5, 40.0, false),
            ('P1','sale', 10.0, 2, 20.0, false),
            ('P1','sale', 12.0, 1, 12.0, false),
            ('P1','sale', 10.0, 1, 10.0, false),
            ('P1','sale', 10.0, 1, 10.0, false)
        ) as t(product_key, line_type, unit_price, quantity, line_amount, is_extreme_line)
        """
    )
    con.execute("create table dim_product as select 'P1' product_key, 'Widget' product_name")
    return con


def test_realization_gap_is_below_median_shortfall():
    con = _synthetic_con()
    gap = dispersion.realization_gap(con, min_lines=3)
    # median price = 10; only the price-8 line is below -> (10-8)*5 = 10.
    assert len(gap) == 1
    assert gap["realization_gap_gbp"].iloc[0] == pytest.approx(10.0)


def test_product_price_stats_counts_prices():
    con = _synthetic_con()
    stats = dispersion.product_price_stats(con, min_lines=3)
    row = stats.iloc[0]
    assert row["n_prices"] == 3
    assert row["price_median"] == pytest.approx(10.0)


def test_ols_slope_recovers_known_relationship():
    rng = np.random.default_rng(0)
    x = rng.normal(0, 1, 500)
    y = -1.3 * x + rng.normal(0, 0.05, 500)
    slope, lo, hi = price_response._ols_slope(x, y)
    assert slope == pytest.approx(-1.3, abs=0.02)
    assert lo < -1.3 < hi


def test_opportunities_frame_ranges_are_ordered():
    opp = Opportunity(
        key="k", name="n", observation="o", hypothesis="h",
        gap_gbp=1000.0, impact_low_gbp=200.0, impact_high_gbp=500.0,
        assumptions=[], confounders=[], margin_low_gbp=90.0, margin_high_gbp=225.0,
    )
    df = opportunities_frame([opp], net_rev=100000.0)
    r = df.iloc[0]
    assert r["impact_low_gbp"] < r["impact_high_gbp"]
    assert r["margin_scenario_low_gbp"] < r["impact_low_gbp"]  # margin < revenue
    assert r["impact_low_pct_rev"] == pytest.approx(0.2)


def test_workbook_has_live_formulas(tmp_path):
    from openpyxl import load_workbook

    power = PowerResult(0.05, 0.8, 0.05, 103.0, 97.0, 0.053, 21000, 42000)
    design = design_price_experiment(
        power, eligible_products=3427, weeks_available=8,
        mde_available_unadjusted=0.278, mde_available_adjusted=0.176,
        preperiod_correlation=0.775,
    )
    path = write_sizing_workbook(tmp_path / "wb.xlsx", power, design, 153.0)
    ws = load_workbook(path).active
    formulas = [ws[f"B{r}"].value for r in range(13, 23)]
    assert all(isinstance(f, str) and f.startswith("=") for f in formulas)
    assert any("NORMSINV" in f for f in formulas)


def test_no_causal_guard_passes_compliant_text():
    _assert_no_causal_elasticity("This is an association. It is not a price elasticity.")


def test_no_causal_guard_rejects_bare_elasticity_claim():
    with pytest.raises(AssertionError):
        _assert_no_causal_elasticity(
            "The price elasticity is -1.5, so cutting price lifts revenue."
        )
