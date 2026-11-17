"""Build comparisons from config, run every bridge and render the M2 findings report."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb
import pandas as pd

from commercial_intelligence.common.config import load_settings
from commercial_intelligence.common.log_utils import get_logger, kv
from commercial_intelligence.revenue.engine import (
    Comparison,
    Period,
    build_customer_bridge,
    build_product_bridge,
    customer_bridge_frame,
    geography_bridge_frame,
    monthly_series,
    product_bridge_frame,
)

log = get_logger(__name__)

RESIDUAL_TOLERANCE_GBP = 1.0  # float dust in the price/volume/mix lens


def comparisons_from_settings() -> list[Comparison]:
    rev = load_settings()["revenue"]
    out = []
    for key in ("yoy", "mom"):
        out.append(
            Comparison(
                name=key,
                label=rev[f"{key}_label"],
                base=Period(
                    f"base_{key}", rev[f"{key}_base_start"], rev[f"{key}_base_end"]
                ),
                current=Period(
                    f"current_{key}", rev[f"{key}_current_start"], rev[f"{key}_current_end"]
                ),
            )
        )
    return out


def build_all(
    con: duckdb.DuckDBPyConnection, comparisons: list[Comparison]
) -> dict[str, pd.DataFrame]:
    bridges: list[pd.DataFrame] = []
    for cmp in comparisons:
        pvm, cb, cc = build_product_bridge(con, cmp)
        bridges.append(product_bridge_frame(pvm, cb, cc, cmp))
        bridges.append(customer_bridge_frame(build_customer_bridge(con, cmp), cmp))
        bridges.append(geography_bridge_frame(con, cmp))
        log.info(
            kv(
                "bridge_built",
                comparison=cmp.name,
                change=round(pvm.current_gross + cc - pvm.base_gross - cb, 2),
                pvm_residual=round(pvm.residual, 4),
            )
        )
    return {
        "bridges": pd.concat(bridges, ignore_index=True),
        "monthly": monthly_series(con),
    }


def _fmt(v: float) -> str:
    return f"{v:,.0f}"


def _bridge_md(df: pd.DataFrame) -> str:
    lines = ["| Component | Value (GBP) | Type |", "| --- | ---: | --- |"]
    for _, r in df.iterrows():
        lines.append(f"| {r['component']} | {r['value_gbp']:,.2f} | {r['kind']} |")
    return "\n".join(lines)


def render_report(con: duckdb.DuckDBPyConnection, data: dict[str, pd.DataFrame]) -> str:
    bridges = data["bridges"]
    yoy = bridges[bridges["comparison"] == "yoy"]
    yoy_label = yoy["comparison_label"].iloc[0]
    prod = yoy[yoy["lens"] == "product"].reset_index(drop=True)
    cust = yoy[yoy["lens"] == "customer"].reset_index(drop=True)
    geo = yoy[yoy["lens"] == "geography"].reset_index(drop=True)

    base_net = prod.loc[prod["kind"] == "start", "value_gbp"].iloc[0]
    end_net = prod.loc[prod["kind"] == "end", "value_gbp"].iloc[0]
    change = end_net - base_net
    pct = 100 * change / base_net
    residual = prod.loc[prod["component"] == "Unexplained residual", "value_gbp"].iloc[0]

    def comp(df, name):
        return df.loc[df["component"] == name, "value_gbp"].iloc[0]

    lines = [
        "# M2 — Revenue decomposition (findings)",
        "",
        f"_Generated {date.today().isoformat()} from the DuckDB warehouse. Every "
        "figure is computed by `commercial_intelligence.revenue`; do not edit by hand._",
        "",
        "## Headline",
        "",
        f"Comparing **{yoy_label}**, net product revenue moved from "
        f"**GBP {base_net:,.0f}** to **GBP {end_net:,.0f}**, a change of "
        f"**GBP {change:,.0f} ({pct:+.1f}%)**.",
        "",
        "Three independent lenses each explain this same change exactly. They are "
        "shown separately — a product-mix effect and a customer-change effect are "
        "two *views* of the one change, never added together.",
        "",
        "> **Descriptive, not causal.** These bridges attribute the observed change "
        "arithmetically. The price component is *associated* revenue from higher or "
        "lower realised prices; it is **not** a price elasticity and says nothing "
        "about how volume would respond to a deliberate price change (see M5).",
        "",
        "## Comparison periods",
        "",
        "The data runs 2009-12-01 to 2011-12-09. December 2009 has no prior-year "
        "comparator and December 2011 is a partial month (and carries a large "
        "return spike), so the year-on-year bridge uses the **11 complete months "
        "January–November** of each year. Partial/edge months are excluded, not "
        "pro-rated.",
        "",
        "## Lens A — Product price / volume / mix",
        "",
        "Price, volume and mix are computed on **gross sales** of products sold in "
        "both periods (average realised price = revenue ÷ units). Products new to "
        "the current period and products discontinued since the base period are "
        "separate bars, and returns (cancellations) are their own bar.",
        "",
        "- **Price** = Σ (Pᶜ − Pᵇ)·Qᶜ  · **Volume** = (ΣQᶜ − ΣQᵇ)·P̄ᵇ  · "
        "**Mix** = Σ ΔQₚ·Pᵇₚ − Volume",
        "",
        _bridge_md(prod),
        "",
        f"The unexplained residual is **GBP {residual:,.2f}** "
        f"({abs(residual) / abs(change) * 100 if change else 0:.4f}% of the change) — "
        "rounding dust from the average-price division, included so the waterfall "
        "sums exactly.",
        "",
        "## Lens B — Customer change",
        "",
        "Net revenue split by customer status. Lines without a customer id (about "
        "a fifth of revenue) cannot be attributed to a customer and form a separate "
        "**guest / unidentified** bar.",
        "",
        _bridge_md(cust),
        "",
        f"New customers contributed GBP {comp(cust,'New customers'):,.0f}; lost "
        f"customers removed GBP {-comp(cust,'Lost customers'):,.0f}; retained "
        f"customers changed by GBP {comp(cust,'Retained customers'):,.0f}.",
        "",
        "## Lens C — Geography (UK vs International)",
        "",
        _bridge_md(geo),
        "",
        "## Limitations",
        "",
        "- The decomposition is **descriptive**: it explains what moved, not why. "
        "No causal or elasticity claim is made.",
        "- Average realised price blends list price, quantity-break pricing and "
        "customer mix within a product; the price bar therefore mixes true price "
        "changes with within-product buyer mix. M5 examines price dispersion.",
        "- Guest revenue (~20%) limits how much of the change the customer lens can "
        "attribute to identified behaviour.",
        "- Figures are historical (2010–2011, one UK retailer) and illustrate method.",
        "",
    ]
    return "\n".join(lines)


def write_exports(data: dict[str, pd.DataFrame], export_dir: Path) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    for name, df in data.items():
        df.to_parquet(export_dir / f"{name}.parquet", index=False)
        df.to_csv(export_dir / f"{name}.csv", index=False)
    log.info(kv("revenue_exports_written", dir=str(export_dir), tables=len(data)))
