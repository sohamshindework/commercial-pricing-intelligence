"""M7: the memo/KPI-tree/PRD numbers come from the exports (templated), not hand-typed."""

from __future__ import annotations

import pandas as pd
import pytest

from commercial_intelligence.reporting import exports, memo


@pytest.fixture
def fake_exports(tmp_path, monkeypatch):
    for sub in ("powerbi", "customers", "revenue", "products", "pricing"):
        (tmp_path / sub).mkdir()

    def put(rel, df):
        df.to_parquet(tmp_path / rel)

    put("powerbi/measures_reconciliation.parquet", pd.DataFrame({
        "measure": ["net_revenue", "gross_revenue", "cancellations", "sale_invoices",
                    "cancellation_invoices", "all_invoices", "gross_sales_aov",
                    "active_customers", "units_sold"],
        "dax_measure": ["[x]"] * 9,
        "python_value": [20_000_000.0, 21_000_000.0, -1_000_000.0, 50_000.0,
                         8_000.0, 58_000.0, 420.0, 5_000.0, 10_000_000.0],
    }))
    put("customers/rfm_customers.parquet",
        pd.DataFrame({"customer_key": [1, 2, 3, 4], "frequency": [1, 2, 2, 3]}))
    put("revenue/monthly.parquet", pd.DataFrame({
        "year_month": ["2011-01", "2011-02"],
        "gross_revenue": [10_500_000.0, 10_500_000.0],
        "cancellations": [-500_000.0, -500_000.0],
        "net_revenue": [10_000_000.0, 10_000_000.0],
        "is_partial_month": [False, False],
    }))

    def bridge_rows(lens, comps):
        rows = [{"lens": lens, "comparison": "yoy", "comparison_label": "YoY test",
                 "component": "Base net revenue", "kind": "start", "step_order": 0,
                 "value_gbp": 19_000_000.0}]
        for i, (c, v) in enumerate(comps, start=1):
            rows.append({"lens": lens, "comparison": "yoy", "comparison_label": "YoY test",
                         "component": c, "kind": "delta", "step_order": i, "value_gbp": v})
        rows.append({"lens": lens, "comparison": "yoy", "comparison_label": "YoY test",
                     "component": "Current net revenue", "kind": "end",
                     "step_order": len(comps) + 1, "value_gbp": 20_000_000.0})
        return rows

    bridges = bridge_rows("product", [
        ("Price", -100_000.0), ("Volume", -1_400_000.0), ("Mix", 400_000.0),
        ("New products", 2_000_000.0), ("Discontinued products", -600_000.0),
    ]) + bridge_rows("customer", [
        ("New customers", 1_300_000.0), ("Lost customers", -1_000_000.0),
        ("Retained customers", -300_000.0),
    ])
    put("revenue/bridges.parquet", pd.DataFrame(bridges))

    put("customers/clv_evaluation_metrics.parquet", pd.DataFrame({
        "method": ["BG/NBD + Gamma-Gamma", "Baseline (historical avg value)"],
        "mae": [100.0, 120.0], "rmse": [150.0, 180.0],
        "predicted_total": [1, 1], "actual_total": [1, 1],
    }))
    put("customers/retention_curve.parquet",
        pd.DataFrame({"month_offset": [0, 1], "avg_retention": [1.0, 0.2], "cohorts": [10, 9]}))
    put("products/metrics_summary.parquet", pd.DataFrame({
        "method": ["Baseline (TF-IDF + LogReg)"],
        "accuracy": [0.88], "macro_f1": [0.87],
        "weighted_f1": [0.88], "n": [147],
    }))
    put("pricing/opportunities.parquet", pd.DataFrame({
        "key": ["price_realization", "discount_leakage"],
        "name": ["Price realisation test", "Discount leakage"],
        "measured_gap_gbp": [2_000_000.0, 4_000.0],
        "impact_low_gbp": [400_000.0, 800.0], "impact_high_gbp": [1_000_000.0, 2_000.0],
        "impact_low_pct_rev": [2.0, 0.0], "impact_high_pct_rev": [5.0, 0.0],
        "margin_scenario_low_gbp": [180_000.0, 360.0],
        "margin_scenario_high_gbp": [450_000.0, 900.0],
    }))
    put("pricing/experiment_summary.parquet", pd.DataFrame([{
        "metric": "average_weekly_gross_sales_revenue_per_sku",
        "baseline_mean_gbp": 100.0, "baseline_sd_gbp": 250.0,
        "target_mde_relative": 0.05, "alpha": 0.05, "power": 0.8,
        "required_products_per_arm": 20_000, "available_products_per_arm": 1_700,
        "mde_available_relative": 0.18, "adequately_powered": False,
        "duration_weeks": 8,
    }]))

    monkeypatch.setattr(exports, "_exports_root", lambda: tmp_path)
    exports.headline_kpis.cache_clear()
    yield
    exports.headline_kpis.cache_clear()


def test_memo_numbers_appear_in_memo(fake_exports):
    n = memo.memo_numbers()
    text = memo.render_memo(n)
    # Each key figure, formatted the same way, must be present in the memo.
    assert memo._gbpm(20_000_000.0) in text           # net revenue £20.00m
    assert "50,000 sale invoices" in text
    assert f"{memo._gbp(400_000.0)}–{memo._gbp(1_000_000.0)}" in text  # opportunity range
    assert "20,000 SKUs per arm" in text
    assert "162.95" not in text                       # not a real-data value
    assert "GBP 100.00" in text and "GBP 120.00" in text
    assert "macro-F1 0.870" in text
    assert "former LLM score was withdrawn" in text
    assert "20%" in text                              # month-1 retention from the curve


def test_memo_has_required_sections_and_limits(fake_exports):
    text = memo.render_memo(memo.memo_numbers())
    for section in ("Answer first", "Recommendations", "What we do NOT know", "Next steps"):
        assert section in text
    assert "No cost data" in text
    assert "associations" in text.lower()
    assert "not a causal price effect" in text


def test_no_placeholders_left(fake_exports):
    import re

    n = memo.memo_numbers()
    for text in (memo.render_memo(n), memo.render_kpi_tree(n), memo.render_prd(n)):
        for bad in ("TODO", "XXX", "{", "}"):
            assert bad not in text
        # A stray NaN would render as a standalone "nan" token (not inside a word).
        assert not re.search(r"\bnan\b", text, re.IGNORECASE)


def test_kpi_tree_identity_ties(fake_exports):
    n = memo.memo_numbers()
    # Sale invoices x gross sales AOV reconciles to gross revenue; cancellations
    # then reconcile gross to net.
    assert n["sale_invoices"] * n["gross_sales_aov"] == pytest.approx(
        n["gross_revenue"], rel=1e-9
    )
    assert n["gross_revenue"] + n["cancellations"] == n["net_revenue"]
    tree = memo.render_kpi_tree(n)
    assert memo._gbpm(n["net_revenue"]) in tree
    assert "Repeat rate" in tree and "75%" in tree


def test_prd_sections(fake_exports):
    prd = memo.render_prd(memo.memo_numbers())
    for s in ("Problem", "Users", "Requirements", "Metrics", "Risks", "Rollout"):
        assert f"## {s}" in prd
    assert "20,000 SKUs per arm" in prd
