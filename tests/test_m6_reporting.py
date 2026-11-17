"""M6: reporting data-access layer (CI-safe with synthetic exports) + export recon."""

from __future__ import annotations

import pandas as pd
import pytest

from commercial_intelligence.reporting import exports


@pytest.fixture
def fake_exports(tmp_path, monkeypatch):
    """A minimal exports tree so the loaders can be tested without the full pipeline."""
    (tmp_path / "powerbi").mkdir()
    (tmp_path / "customers").mkdir()
    (tmp_path / "revenue").mkdir()

    pd.DataFrame(
        {"measure": ["net_revenue", "gross_revenue", "cancellations", "sale_invoices",
                     "cancellation_invoices", "all_invoices", "gross_sales_aov",
                     "active_customers", "units_sold"],
         "dax_measure": ["[Net Revenue]"] * 9,
         "python_value": [1000.0, 1100.0, -100.0, 10.0, 2.0, 12.0, 110.0, 8.0, 500.0]}
    ).to_parquet(tmp_path / "powerbi" / "measures_reconciliation.parquet")

    pd.DataFrame({"customer_key": [1, 2, 3, 4], "frequency": [1, 2, 3, 1]}).to_parquet(
        tmp_path / "customers" / "rfm_customers.parquet"
    )

    pd.DataFrame(
        {"lens": ["product", "product", "customer"],
         "comparison": ["yoy", "yoy", "yoy"],
         "comparison_label": ["YoY"] * 3,
         "component": ["Base net revenue", "Current net revenue", "Base net revenue"],
         "kind": ["start", "end", "start"],
         "step_order": [0, 1, 0],
         "value_gbp": [900.0, 1000.0, 900.0]}
    ).to_parquet(tmp_path / "revenue" / "bridges.parquet")

    monkeypatch.setattr(exports, "_exports_root", lambda: tmp_path)
    exports.headline_kpis.cache_clear()
    yield tmp_path
    exports.headline_kpis.cache_clear()


def test_missing_export_raises():
    with pytest.raises(exports.MissingExportError):
        exports._read("nope/missing.parquet")


def test_bridge_filters_lens_and_comparison(fake_exports):
    prod = exports.bridge("product", "yoy")
    assert set(prod["lens"]) == {"product"}
    assert len(prod) == 2


def test_headline_kpis(fake_exports):
    k = exports.headline_kpis()
    assert k["net_revenue"] == 1000.0
    assert k["sale_invoices"] == 10.0
    assert k["cancellation_invoices"] == 2.0
    assert k["gross_sales_aov"] == 110.0
    assert k["active_customers"] == 8.0
    # repeat rate = share of rfm with frequency >= 2 -> 2 of 4.
    assert k["repeat_rate"] == pytest.approx(0.5)
    # YoY % = (1000-900)/900.
    assert k["yoy_pct"] == pytest.approx(100 / 9, abs=0.01)


def _load_export_powerbi():
    import importlib.util

    from commercial_intelligence.common.config import REPO_ROOT

    spec = importlib.util.spec_from_file_location(
        "export_powerbi", REPO_ROOT / "scripts" / "export_powerbi.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_export_reconciliation_against_warehouse(con):
    export_powerbi = _load_export_powerbi()
    recon = export_powerbi._reconciliation(con)
    assert list(recon.columns) == ["measure", "dax_measure", "python_value"]
    net = recon.loc[recon["measure"] == "net_revenue", "python_value"].iloc[0]
    assert net > 0
    assert set(recon["measure"]) >= {
        "net_revenue", "gross_revenue", "cancellations", "sale_invoices",
        "cancellation_invoices", "gross_sales_aov", "active_customers",
    }


def test_invoice_metrics_handle_sales_cancellations_and_mixed_invoice():
    import duckdb

    con = duckdb.connect()
    con.execute(
        """
        create table fct_order_lines as select * from (values
            ('S1', 'sale', 100.0, 1, 1),
            ('S1', 'sale', 50.0, 1, 2),
            ('S2', 'sale', 80.0, 2, 3),
            ('C1', 'cancellation', -20.0, -1, 4),
            ('M1', 'sale', 40.0, 1, 5),
            ('M1', 'cancellation', -10.0, -1, 5)
        ) as t(invoice_no, line_type, line_amount, quantity, customer_key)
        """
    )
    recon = _load_export_powerbi()._reconciliation(con).set_index("measure")["python_value"]
    assert recon["gross_revenue"] == 270.0
    assert recon["cancellations"] == -30.0
    assert recon["net_revenue"] == 240.0
    assert recon["sale_invoices"] == 3
    assert recon["cancellation_invoices"] == 2
    assert recon["all_invoices"] == 4
    assert recon["gross_sales_aov"] == 90.0
