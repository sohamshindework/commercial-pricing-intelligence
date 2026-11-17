"""M2 acceptance on the sample warehouse: every bridge reconciles to the net change."""

from __future__ import annotations

import pytest

from commercial_intelligence.revenue.engine import (
    build_customer_bridge,
    build_product_bridge,
    customer_bridge_frame,
    geography_bridge_frame,
    product_bridge_frame,
)
from commercial_intelligence.revenue.report import (
    RESIDUAL_TOLERANCE_GBP,
    comparisons_from_settings,
)


@pytest.fixture(scope="module")
def comparisons():
    return comparisons_from_settings()


def _reconciles(df, tol: float) -> float:
    start = df.loc[df["kind"] == "start", "value_gbp"].iloc[0]
    end = df.loc[df["kind"] == "end", "value_gbp"].iloc[0]
    deltas = df.loc[df["kind"] == "delta", "value_gbp"].sum()
    residual = start + deltas - end
    assert abs(residual) <= tol, f"bridge does not close: {residual}"
    return residual


def test_net_revenue_matches_engine_periods(con, comparisons):
    # The product bridge's start/end nets must equal a direct SQL net-revenue sum.
    for cmp in comparisons:
        pvm, cb, cc = build_product_bridge(con, cmp)
        for period, cancel, gross in (
            (cmp.base, cb, pvm.base_gross),
            (cmp.current, cc, pvm.current_gross),
        ):
            (direct,) = con.execute(
                "select coalesce(sum(line_amount),0) from fct_order_lines "
                "where invoice_date between ? and ?",
                [period.start, period.end],
            ).fetchone()
            assert abs(float(direct) - (gross + cancel)) <= 0.01


def test_product_bridge_closes(con, comparisons):
    for cmp in comparisons:
        pvm, cb, cc = build_product_bridge(con, cmp)
        df = product_bridge_frame(pvm, cb, cc, cmp)
        _reconciles(df, tol=0.01)  # residual column closes any float dust
        assert abs(pvm.residual) <= RESIDUAL_TOLERANCE_GBP


def test_customer_bridge_closes_exactly(con, comparisons):
    for cmp in comparisons:
        df = customer_bridge_frame(build_customer_bridge(con, cmp), cmp)
        # No average-price division in this lens: it must close to the penny.
        _reconciles(df, tol=0.01)


def test_geography_bridge_closes_exactly(con, comparisons):
    for cmp in comparisons:
        df = geography_bridge_frame(con, cmp)
        _reconciles(df, tol=0.01)


def test_all_three_lenses_agree_on_total_change(con, comparisons):
    for cmp in comparisons:
        pvm, cb, cc = build_product_bridge(con, cmp)
        prod = product_bridge_frame(pvm, cb, cc, cmp)
        cust = customer_bridge_frame(build_customer_bridge(con, cmp), cmp)
        geo = geography_bridge_frame(con, cmp)

        def change(df):
            end = df.loc[df["kind"] == "end", "value_gbp"].iloc[0]
            start = df.loc[df["kind"] == "start", "value_gbp"].iloc[0]
            return round(end - start, 2)

        assert change(prod) == change(cust) == change(geo)


def test_returns_component_is_cancellation_change(con, comparisons):
    cmp = comparisons[0]
    pvm, cb, cc = build_product_bridge(con, cmp)
    df = product_bridge_frame(pvm, cb, cc, cmp)
    returns = df.loc[df["component"] == "Returns (cancellations)", "value_gbp"].iloc[0]
    assert abs(returns - round(cc - cb, 2)) <= 0.01
