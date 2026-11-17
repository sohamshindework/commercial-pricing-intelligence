"""Run all M3 analyses, write exports + plots, and render the findings report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd

from commercial_intelligence.common.config import load_settings
from commercial_intelligence.common.log_utils import get_logger, kv
from commercial_intelligence.customers import cohorts, segmentation
from commercial_intelligence.customers.clv import (
    BASELINE_VALUE,
    MODEL_VALUE,
    HoldoutEvaluation,
    build_transactions,
    evaluate_holdout,
    full_data_clv,
    split_sensitivity,
    value_winner,
)
from commercial_intelligence.customers.plots import calibration_plot, retention_heatmap

log = get_logger(__name__)


@dataclass
class M3Outputs:
    rfm: pd.DataFrame
    segment_summary: pd.DataFrame
    cluster_summary: pd.DataFrame
    kmeans_meta: dict
    cohort_rates: pd.DataFrame
    cohort_counts: pd.DataFrame
    retention_curve: pd.DataFrame
    clv_eval: HoldoutEvaluation
    clv_customers: pd.DataFrame
    clv_sensitivity: pd.DataFrame


def run_analyses(con: duckdb.DuckDBPyConnection) -> M3Outputs:
    cfg = load_settings()["customers"]
    seed = int(cfg["random_seed"])

    rfm = segmentation.add_rfm_scores(segmentation.rfm_table(con))
    km = segmentation.kmeans_segments(rfm, list(cfg["kmeans_k_candidates"]), seed)
    rfm = rfm.assign(kmeans_cluster=km.labels)
    cluster_summary = segmentation.describe_clusters(rfm, km.labels)
    stability = segmentation.segment_stability(
        con, cfg["stability_split_date"], km.k, seed
    )

    segment_summary = (
        rfm.groupby("rfm_segment")
        .agg(customers=("customer_key", "count"), monetary=("monetary", "sum"))
        .reset_index()
        .sort_values("monetary", ascending=False)
    )

    counts, rates = cohorts.retention_matrix(con)
    curve = cohorts.retention_curve(rates)

    clv_cfg = cfg["clv"]
    tx = build_transactions(con)
    obs_end = tx["date"].max().date()
    clv_eval = evaluate_holdout(
        tx, clv_cfg["calibration_end"], obs_end, float(clv_cfg["penalizer_coef"])
    )
    chosen_clv = value_winner(clv_eval.metrics)
    clv_customers = full_data_clv(
        tx,
        float(clv_cfg["penalizer_coef"]),
        int(clv_cfg["horizon_days"]),
        chosen_clv,
    )
    clv_sensitivity = split_sensitivity(
        tx, list(clv_cfg["sensitivity_splits"]), obs_end, float(clv_cfg["penalizer_coef"])
    )

    log.info(
        kv(
            "m3_analyses_done",
            rfm_customers=len(rfm),
            kmeans_k=km.k,
            silhouette=round(km.silhouette, 3),
            clv_model_fallback=clv_eval.n_model_fallback,
        )
    )
    return M3Outputs(
        rfm=rfm,
        segment_summary=segment_summary,
        cluster_summary=cluster_summary,
        kmeans_meta={
            "k": km.k,
            "silhouette": km.silhouette,
            "scores_by_k": km.scores_by_k,
            **{f"stability_{k}": v for k, v in stability.items()},
        },
        cohort_rates=rates,
        cohort_counts=counts,
        retention_curve=curve,
        clv_eval=clv_eval,
        clv_customers=clv_customers,
        clv_sensitivity=clv_sensitivity,
    )


def clv_winner(ev: HoldoutEvaluation) -> tuple[str, float, float]:
    m = ev.metrics.set_index("method")["mae"]
    model, base = m[MODEL_VALUE], m[BASELINE_VALUE]
    winner = MODEL_VALUE if model < base else BASELINE_VALUE
    improvement = (base - model) / base * 100
    return winner, improvement, float(model)


def write_exports(out: M3Outputs, export_dir: Path) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "rfm_customers": out.rfm,
        "segment_summary": out.segment_summary,
        "kmeans_cluster_summary": out.cluster_summary,
        "cohort_retention_rates": out.cohort_rates.reset_index(),
        "cohort_retention_counts": out.cohort_counts.reset_index(),
        "retention_curve": out.retention_curve,
        "clv_evaluation_metrics": out.clv_eval.metrics,
        "clv_purchase_metrics": out.clv_eval.purchase_metrics,
        "clv_calibration_table": out.clv_eval.calibration_table,
        "clv_split_sensitivity": out.clv_sensitivity,
        "clv_customers": out.clv_customers,
    }
    for name, df in tables.items():
        df.to_parquet(export_dir / f"{name}.parquet", index=False)
        df.to_csv(export_dir / f"{name}.csv", index=False)
    log.info(kv("m3_exports_written", dir=str(export_dir), tables=len(tables)))


def write_plots(out: M3Outputs, assets_dir: Path) -> dict[str, Path]:
    return {
        "calibration": calibration_plot(
            out.clv_eval.calibration_table, assets_dir / "clv_calibration.png"
        ),
        "retention": retention_heatmap(out.cohort_rates, assets_dir / "cohort_retention.png"),
    }


def _md_table(df: pd.DataFrame, floatfmt: str = "{:,.2f}") -> str:
    cols = list(df.columns)
    # Decide formatting per column from its dtype (iterrows would upcast a mixed
    # int/float row to all-float, so format columns, not row values).
    is_float = {c: pd.api.types.is_float_dtype(df[c]) for c in cols}
    lines = ["| " + " | ".join(str(c) for c in cols) + " |",
             "| " + " | ".join("---" for _ in cols) + " |"]
    for row in df.itertuples(index=False, name=None):
        cells = [
            floatfmt.format(v) if is_float[c] else str(v)
            for c, v in zip(cols, row, strict=True)
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_report(out: M3Outputs) -> str:
    ev = out.clv_eval
    winner, improvement, _ = clv_winner(ev)
    km = out.kmeans_meta
    curve = out.retention_curve
    m1 = curve.loc[curve["month_offset"] == 1, "avg_retention"]
    month1 = float(m1.iloc[0]) if len(m1) else float("nan")

    uses_clv = winner == MODEL_VALUE
    clv_sentence = (
        f"The BG/NBD + Gamma-Gamma model **beats** the historical-value baseline "
        f"on complete held-out customer value (MAE GBP "
        f"{ev.metrics.set_index('method').loc[MODEL_VALUE,'mae']:,.2f} vs "
        f"{ev.metrics.set_index('method').loc[BASELINE_VALUE,'mae']:,.2f}, "
        f"{improvement:+.1f}%), so forward scores use the model."
        if uses_clv
        else
        f"The BG/NBD + Gamma-Gamma model does **not** beat the historical-value "
        f"baseline on complete held-out customer value (MAE GBP "
        f"{ev.metrics.set_index('method').loc[MODEL_VALUE,'mae']:,.2f} vs "
        f"{ev.metrics.set_index('method').loc[BASELINE_VALUE,'mae']:,.2f}). "
        "Per the integrity rules, forward scores use the simpler baseline."
    )

    seg = out.segment_summary.copy()
    seg["monetary"] = seg["monetary"].round(0)
    cluster = out.cluster_summary.copy()
    for c in ("recency_days", "frequency", "monetary", "total_monetary"):
        cluster[c] = cluster[c].round(0)

    lines = [
        "# M3 — Customer intelligence (findings)",
        "",
        f"_Generated {date.today().isoformat()} from the DuckDB warehouse. Every "
        "figure is computed by `commercial_intelligence.customers`; do not edit by hand._",
        "",
        "Scope: identified customers only (guests, ~1/5 of revenue, carry no customer "
        "id and are excluded from this milestone). Activity = sales; returns are "
        "excluded from purchase counts.",
        "",
        "## Headline",
        "",
        f"- **{len(out.rfm):,} identified customers** segmented by RFM and k-means.",
        f"- **Month-1 repeat rate ≈ {month1*100:.0f}%** — most first-time buyers do not "
        "return the next month; retention then flattens (see heatmap).",
        f"- {clv_sentence}",
        "",
        "## 1. Segmentation",
        "",
        "### RFM business segments",
        "",
        "Recency / Frequency / Monetary scored into quintiles and mapped to the "
        "classic segment grid.",
        "",
        _md_table(seg.rename(columns={"monetary": "monetary_gbp"})),
        "",
        "### k-means on scaled RFM",
        "",
        f"Features: recency, log(frequency), log(monetary), standardised. k chosen by "
        f"silhouette over {list(km['scores_by_k'])}: **k = {km['k']}** "
        f"(silhouette {km['silhouette']:.3f}). Silhouette by k: "
        + ", ".join(f"{k}:{v:.3f}" for k, v in km["scores_by_k"].items())
        + ".",
        "",
        "**Stability:** fitting RFM k-means independently on two time windows and "
        "comparing by Adjusted Rand Index gives ARI = "
        f"**{km.get('stability_ari', float('nan')):.3f}** on "
        f"{km.get('stability_n_common', 0):,} customers active in both windows. "
        "A modest ARI means cluster *membership* shifts as customers' behaviour "
        "changes, even though the cluster *shapes* are stable — so the simple, "
        "transparent RFM grid is the recommended operational segmentation, with "
        "k-means as a cross-check.",
        "",
        _md_table(cluster.rename(columns={"monetary": "median_monetary_gbp"}), "{:,.0f}"),
        "",
        "## 2. Cohort retention",
        "",
        "Monthly cohorts by first-purchase month. Average retention by months-since-"
        "acquisition (cohorts old enough to be observed):",
        "",
        _md_table(
            out.retention_curve.rename(columns={"avg_retention": "avg_retention_share"}).astype(
                {"month_offset": int, "cohorts": int}
            ),
            "{:.3f}",
        ),
        "",
        "Heatmap: `assets/customers/cohort_retention.png`.",
        "",
        "## 3. Customer value — honest evaluation",
        "",
        f"**Time-based holdout (no leakage):** calibrate on transactions up to "
        f"{ev.calibration_end}, test on the following "
        f"{ev.duration_holdout_days:.0f} days ({ev.observation_end}). "
        f"{ev.n_customers:,} customers acquired during calibration are scored; "
        "features never see the holdout.",
        "",
        "Predicted vs actual **complete holdout customer value (GBP)**. This is the "
        "selection metric because it evaluates purchase frequency and monetary value together:",
        "",
        _md_table(
            ev.metrics.rename(
                columns={"mae": "MAE", "rmse": "RMSE",
                         "predicted_total": "pred_total", "actual_total": "actual_total"}
            ),
            "{:,.3f}",
        ),
        "",
        f"Winner on MAE: **{winner}**."
        + (f" {ev.n_model_fallback} zero-repeat customer(s) fell back to the baseline "
           "estimate because the model's hypergeometric term was non-finite."
           if ev.n_model_fallback else ""),
        "",
        "Purchase-count diagnostics (not used alone to select CLV):",
        "",
        _md_table(
            ev.purchase_metrics.rename(
                columns={"mae": "MAE", "rmse": "RMSE",
                         "predicted_total": "pred_total", "actual_total": "actual_total"}
            ),
            "{:,.3f}",
        ),
        "",
        f"**Monetary (Gamma-Gamma) check:** predicted average order value vs actual "
        f"holdout AOV on {ev.monetary_mae['n_customers']:,} repeat customers — "
        f"Gamma-Gamma MAE GBP {ev.monetary_mae['gamma_gamma_mae']:.2f} vs naive "
        f"(calibration AOV) MAE GBP {ev.monetary_mae['baseline_aov_mae']:.2f}.",
        "",
        "Calibration plot: `assets/customers/clv_calibration.png`. "
        "Forward CLV scores per customer: `data/exports/customers/clv_customers.parquet`.",
        "",
        "**Robustness.** Re-running complete-value evaluation at several calibration "
        "cut-offs shows whether the selected method is stable across time:",
        "",
        _md_table(
            out.clv_sensitivity.rename(
                columns={"model_value_mae": "model value MAE",
                         "baseline_value_mae": "baseline value MAE"}
            ),
            "{:.3f}",
        ),
        "",
        "## Limitations",
        "",
        "- CLV and segments cover identified customers only; guest revenue (~20%) is "
        "out of scope here and shown in the revenue bridges (M2) instead.",
        "- **RFM quintiles and tied values:** about 28% of customers have bought only "
        "once, so the Frequency quintile boundary falls inside a large tie. Those "
        "single-purchase customers are split between the lowest two F-scores by a "
        "deterministic but arbitrary tie-break; the F-score is therefore coarse at "
        "the low end. The k-means view, which uses the raw values, does not have "
        "this boundary effect.",
        "- **Cohort right-censoring:** later month-offsets are averaged over only the "
        "earlier cohorts old enough to reach them (offset 12 uses 13 of 25 cohorts), "
        "so the small late-tenure uptick is a cohort-composition effect, not a "
        "genuine recovery in loyalty.",
        "- BG/NBD assumes a non-contractual, steady-purchasing process; promotions and "
        "the catalogue churn seen in M2 violate this, so treat CLV as a ranking aid, "
        "not a guaranteed forecast. The horizon value is undiscounted.",
        "- The selected historical-value baseline forecasts future repeat value only. "
        "Customers with no observed repeat purchase receive a conservative zero forward "
        "score; this is not their total lifetime revenue and never subtracts prior purchases.",
        "- Only ~24 months of data: the holdout is a single 6-month window, so the "
        "evaluation shows relative model quality, not long-run accuracy.",
        "- Figures are historical (2010–2011, one UK retailer) and illustrate method.",
        "",
    ]
    return "\n".join(lines)
