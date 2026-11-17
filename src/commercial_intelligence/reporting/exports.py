"""Load the milestone exports. Pure pandas (no web framework), so it is unit-testable."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from commercial_intelligence.common.config import load_settings, repo_path


class MissingExportError(FileNotFoundError):
    """Raised when an expected export is absent (run the milestone scripts first)."""


def _exports_root() -> Path:
    return repo_path(load_settings()["app"]["exports_root"])


def _read(rel: str) -> pd.DataFrame:
    path = _exports_root() / rel
    if not path.exists():
        raise MissingExportError(
            f"Required analytical export {rel!r} is unavailable. "
            "Run the documented analytical pipeline."
        )
    return pd.read_parquet(path)


# ---- revenue (M2) ----------------------------------------------------------
def monthly_revenue() -> pd.DataFrame:
    return _read("revenue/monthly.parquet")


def revenue_bridges() -> pd.DataFrame:
    return _read("revenue/bridges.parquet")


def bridge(lens: str, comparison: str = "yoy") -> pd.DataFrame:
    b = revenue_bridges()
    return b[(b["lens"] == lens) & (b["comparison"] == comparison)].reset_index(drop=True)


# ---- customers (M3) --------------------------------------------------------
def rfm_customers() -> pd.DataFrame:
    return _read("customers/rfm_customers.parquet")


def segment_summary() -> pd.DataFrame:
    return _read("customers/segment_summary.parquet")


def retention_curve() -> pd.DataFrame:
    return _read("customers/retention_curve.parquet")


def cohort_rates() -> pd.DataFrame:
    return _read("customers/cohort_retention_rates.parquet")


def cohort_counts() -> pd.DataFrame:
    return _read("customers/cohort_retention_counts.parquet")


def clv_metrics() -> pd.DataFrame:
    return _read("customers/clv_evaluation_metrics.parquet")


def clv_customers() -> pd.DataFrame:
    return _read("customers/clv_customers.parquet")


# ---- products (M4) ---------------------------------------------------------
def product_metrics() -> pd.DataFrame:
    return _read("products/metrics_summary.parquet")


def product_families() -> pd.DataFrame:
    return _read("products/product_families.parquet")


def per_class_baseline() -> pd.DataFrame:
    return _read("products/per_class_baseline.parquet")


# ---- pricing (M5) ----------------------------------------------------------
def price_dispersion() -> pd.DataFrame:
    return _read("pricing/price_dispersion_products.parquet")


def opportunities() -> pd.DataFrame:
    return _read("pricing/opportunities.parquet")


def price_response() -> pd.DataFrame:
    return _read("pricing/price_response_by_family.parquet")


def experiment_summary() -> pd.DataFrame:
    return _read("pricing/experiment_summary.parquet")


# ---- powerbi reconciliation + aggregates (M6) -----------------------------
def reconciliation() -> pd.DataFrame:
    return _read("powerbi/measures_reconciliation.parquet")


def revenue_by_family() -> pd.DataFrame:
    return _read("powerbi/revenue_by_family.parquet")


def top_products() -> pd.DataFrame:
    return _read("powerbi/top_products.parquet")


@lru_cache(maxsize=1)
def headline_kpis() -> dict[str, float]:
    """Top-line numbers for the overview, all from validated exports."""
    recon = reconciliation().set_index("measure")["python_value"]
    rfm = rfm_customers()
    repeat_rate = float((rfm["frequency"] >= 2).mean())

    prod = bridge("product")
    start = float(prod.loc[prod["kind"] == "start", "value_gbp"].iloc[0])
    end = float(prod.loc[prod["kind"] == "end", "value_gbp"].iloc[0])
    yoy_pct = (end - start) / start * 100 if start else 0.0

    return {
        "net_revenue": float(recon["net_revenue"]),
        "gross_revenue": float(recon["gross_revenue"]),
        "cancellations": float(recon["cancellations"]),
        "sale_invoices": float(recon["sale_invoices"]),
        "cancellation_invoices": float(recon["cancellation_invoices"]),
        "all_invoices": float(recon["all_invoices"]),
        "gross_sales_aov": float(recon["gross_sales_aov"]),
        "active_customers": float(recon["active_customers"]),
        "units_sold": float(recon["units_sold"]),
        "repeat_rate": repeat_rate,
        "yoy_pct": yoy_pct,
        "yoy_label": bridge("product")["comparison_label"].iloc[0],
    }
