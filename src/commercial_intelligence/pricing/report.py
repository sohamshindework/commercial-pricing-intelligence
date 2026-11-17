"""Run M5: dispersion, price response, opportunities, experiment, workbook, report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from commercial_intelligence.common.config import load_settings, repo_path
from commercial_intelligence.common.log_utils import get_logger, kv
from commercial_intelligence.pricing import dispersion, opportunities, price_response
from commercial_intelligence.pricing.experiment import (
    ExperimentDesign,
    design_price_experiment,
    minimum_detectable_effect,
    sample_size_statsmodels,
)
from commercial_intelligence.pricing.workbook import write_sizing_workbook
from commercial_intelligence.products.taxonomy import code_to_name

log = get_logger(__name__)

# Terms that would (wrongly) present a descriptive result as causal. "elasticity"
# must appear nowhere; the descriptive sections must say "association".
FORBIDDEN_IN_DESCRIPTIVE = ("elasticity", "price elasticity")


@dataclass
class M5Outputs:
    dispersion_summary: dict
    dispersion_stats: pd.DataFrame
    slopes: pd.DataFrame
    opportunities: pd.DataFrame
    opp_objects: list
    net_revenue: float
    power_result: object
    mde_given_sample: float
    design: ExperimentDesign
    baseline_mean: float
    baseline_sd: float
    cuped_residual_sd: float
    workbook_path: Path


def _sku_block_planning(
    con: duckdb.DuckDBPyConnection, min_lines: int, duration_weeks: int
) -> dict[str, float | int]:
    """Estimate SKU-level outcome variance from dense historical test windows.

    Each candidate SKU has one average-weekly-revenue outcome per non-overlapping
    block. Missing SKU-week sales are genuine zeros. Adjacent blocks supply the
    pre-period and outcome pair used to estimate CUPED/ANCOVA variance reduction.
    """
    df = con.execute(
        """
        with bounds as (
            select
                date_trunc('week', min(invoice_date)) + interval 7 day as first_week,
                date_trunc('week', max(invoice_date)) - interval 7 day as last_week
            from fct_order_lines
        ),
        weeks as (
            select
                row_number() over (order by week_start) - 1 as week_idx,
                week_start
            from bounds, generate_series(first_week, last_week, interval 7 day) t(week_start)
        ),
        cand as (
            select product_key from fct_order_lines
            where line_type = 'sale' and not is_extreme_line
            group by product_key
            having count(*) >= ? and count(distinct unit_price) > 1
        ),
        blocks as (
            select distinct floor(week_idx / ?)::integer as block_id
            from weeks
            where floor(week_idx / ?) < floor((select count(*) from weeks) / ?)
        ),
        grid as (
            select c.product_key, b.block_id from cand c cross join blocks b
        ),
        actual as (
            select
                f.product_key,
                floor(w.week_idx / ?)::integer as block_id,
                sum(f.line_amount) / ? as outcome
            from fct_order_lines f
            join weeks w on date_trunc('week', f.invoice_date) = w.week_start
            join cand using (product_key)
            where f.line_type = 'sale' and not f.is_extreme_line
            group by f.product_key, block_id
        ),
        outcomes as (
            select g.product_key, g.block_id, coalesce(a.outcome, 0) as outcome
            from grid g left join actual a using (product_key, block_id)
        )
        select cur.product_key, cur.block_id, prev.outcome as preperiod, cur.outcome
        from outcomes cur
        join outcomes prev
          on cur.product_key = prev.product_key and cur.block_id = prev.block_id + 1
        """,
        [min_lines, duration_weeks, duration_weeks, duration_weeks,
         duration_weeks, duration_weeks],
    ).df()
    mean = float(df["outcome"].mean())
    sd = float(df["outcome"].std(ddof=1))
    rho = float(df["preperiod"].corr(df["outcome"]))
    theta = float(
        np.cov(df["preperiod"], df["outcome"], ddof=1)[0, 1]
        / np.var(df["preperiod"], ddof=1)
    )
    residual = df["outcome"] - theta * df["preperiod"]
    return {
        "mean": mean,
        "sd": sd,
        "rho": rho,
        "residual_sd": float(residual.std(ddof=1)),
        "eligible_products": int(df["product_key"].nunique()),
        "historical_pairs": int(len(df)),
    }


def run(con: duckdb.DuckDBPyConnection) -> M5Outputs:
    settings = load_settings()
    cfg = settings["pricing"]
    min_lines = int(cfg["min_lines_for_dispersion"])

    families = pd.read_parquet(repo_path(cfg["product_families_path"]))

    stats = dispersion.product_price_stats(con, min_lines)
    disp_summary = dispersion.dispersion_summary(stats)

    lines = price_response.load_sale_lines_with_family(con, families)
    slopes = price_response.slopes_frame(price_response.family_slopes(lines))

    opps, net_rev = opportunities.build_opportunities(con, cfg)
    opp_frame = opportunities.opportunities_frame(opps, net_rev)

    ecfg = cfg["experiment"]
    duration = int(ecfg["weeks_available"])
    planning = _sku_block_planning(con, min_lines, duration)
    mean = float(planning["mean"])
    sd = float(planning["sd"])
    residual_sd = float(planning["residual_sd"])
    eligible = int(planning["eligible_products"])
    power = sample_size_statsmodels(
        mean, residual_sd, float(ecfg["mde_relative"]),
        float(ecfg["alpha"]), float(ecfg["power"])
    )
    available_per_arm = eligible // 2
    mde_unadjusted = minimum_detectable_effect(
        mean, sd, available_per_arm, float(ecfg["alpha"]), float(ecfg["power"])
    )
    mde_given = minimum_detectable_effect(
        mean, residual_sd, available_per_arm, float(ecfg["alpha"]), float(ecfg["power"])
    )
    design = design_price_experiment(
        power,
        eligible_products=eligible,
        weeks_available=duration,
        mde_available_unadjusted=mde_unadjusted,
        mde_available_adjusted=mde_given,
        preperiod_correlation=float(planning["rho"]),
    )

    wb_path = write_sizing_workbook(
        repo_path(cfg["workbook_path"]), power, design, sd
    )

    log.info(kv("m5_done", dispersion_pct=disp_summary["pct_multi_price"],
                n_per_group=power.n_per_group, mde=round(power.mde_relative, 3)))
    return M5Outputs(
        dispersion_summary=disp_summary, dispersion_stats=stats, slopes=slopes,
        opportunities=opp_frame, opp_objects=opps, net_revenue=net_rev,
        power_result=power, mde_given_sample=mde_given, design=design,
        baseline_mean=mean, baseline_sd=sd, workbook_path=wb_path,
        cuped_residual_sd=residual_sd,
    )


def write_exports(out: M5Outputs, export_dir: Path) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    p = out.power_result
    experiment_summary = pd.DataFrame([{
        "metric": "average_weekly_gross_sales_revenue_per_sku",
        "randomisation_unit": "SKU",
        "analysis_unit": "SKU (one aggregated 8-week outcome)",
        "baseline_mean_gbp": round(out.baseline_mean, 2),
        "baseline_sd_gbp": round(out.baseline_sd, 2),
        "cuped_residual_sd_gbp": round(out.cuped_residual_sd, 2),
        "preperiod_correlation": out.design.preperiod_correlation,
        "variance_reduction": out.design.variance_reduction,
        "target_mde_relative": p.mde_relative,
        "alpha": p.alpha,
        "power": p.power,
        "eligible_products": out.design.eligible_products,
        "available_products_per_arm": out.design.available_products_per_arm,
        "required_products_per_arm": out.design.required_products_per_arm,
        "mde_available_unadjusted": out.design.mde_available_unadjusted,
        "mde_available_relative": out.design.mde_available_adjusted,
        "adequately_powered": out.design.adequately_powered,
        "duration_weeks": out.design.duration_weeks,
    }])
    tables = {
        "price_dispersion_products": out.dispersion_stats,
        "price_response_by_family": out.slopes,
        "opportunities": out.opportunities,
        "experiment_summary": experiment_summary,
    }
    for name, df in tables.items():
        df.to_parquet(export_dir / f"{name}.parquet", index=False)
        df.to_csv(export_dir / f"{name}.csv", index=False)
    log.info(kv("m5_exports_written", dir=str(export_dir), tables=len(tables)))


def _md(df: pd.DataFrame, floatfmt: str = "{:,.2f}") -> str:
    cols = list(df.columns)
    is_float = {c: pd.api.types.is_float_dtype(df[c]) for c in cols}
    lines = ["| " + " | ".join(str(c) for c in cols) + " |",
             "| " + " | ".join("---" for _ in cols) + " |"]
    for row in df.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(
            floatfmt.format(v) if is_float[c] else str(v)
            for c, v in zip(cols, row, strict=True)) + " |")
    return "\n".join(lines)


def render_report(out: M5Outputs) -> str:
    names = code_to_name()
    ds = out.dispersion_summary
    power = out.power_result
    design = out.design
    slopes = out.slopes.copy()
    slopes["family"] = slopes["family_code"].map(names)

    opp_lines = []
    for o in out.opp_objects:
        opp_lines += [
            f"### {o.name}",
            "",
            f"- **Observation (descriptive):** {o.observation}",
            f"- **Hypothesis (action):** {o.hypothesis}",
            f"- **Scenario revenue range:** GBP {o.impact_low_gbp:,.0f} – "
            f"{o.impact_high_gbp:,.0f} "
            f"({100*o.impact_low_gbp/out.net_revenue:.2f}%–"
            f"{100*o.impact_high_gbp/out.net_revenue:.2f}% "
            "of net revenue), under the assumptions below.",
            f"- **Margin scenario (assumed cost ratio, illustrative only):** GBP "
            f"{o.margin_low_gbp:,.0f} – {o.margin_high_gbp:,.0f}.",
            "- **Assumptions:** " + " ".join(f"({i+1}) {a}" for i, a in enumerate(o.assumptions)),
            "- **Confounders / caveats:** " + " ".join(o.confounders),
            "- **Validation:** causal effect unknown until tested by the experiment below.",
            "",
        ]

    lines = [
        "# M5 — Pricing opportunities and experiment design (findings)",
        "",
        f"_Generated {date.today().isoformat()} by `commercial_intelligence.pricing`._",
        "",
        "> **Non-causal.** Every price-quantity relationship here is a descriptive "
        "**association** from observational data. No price elasticity is estimated and no "
        "number states the revenue effect of a deliberate price change. Revenue "
        "opportunities are **scenario ranges under stated assumptions**, not forecasts. "
        "Margin figures are a labelled scenario only — there is no cost data. A causal "
        "effect can be established only by the randomised experiment specified below.",
        "",
        "## 1. Price dispersion",
        "",
        f"Of {ds['products_analysed']:,} products with enough sale history, "
        f"**{ds['pct_multi_price']}%** are sold at more than one unit price "
        f"(median within-product price coefficient of variation "
        f"{ds['median_price_cv']:.2f}). This dispersion is the raw material for the "
        "opportunities below. Full table: `data/exports/pricing/price_dispersion_products.csv`.",
        "",
        "## 2. Descriptive price–quantity association by family",
        "",
        "Log-log association between unit price and quantity, by family. The "
        "**within-product** slope uses only price variation for the *same product over time* "
        "(product fixed effects); it is the more comparable figure but remains an "
        "**association**, confounded by quantity-break pricing, seasonality and customer mix. "
        "It is **not** a price elasticity.",
        "",
        _md(slopes[["family_code", "family", "n_lines", "n_products",
                    "pooled_slope", "within_slope", "within_ci_low", "within_ci_high"]],
            "{:.3f}"),
        "",
        "Negative slopes mean larger quantities are associated with lower unit prices — "
        "consistent with bulk discounting, which is a confounder, not a demand response.",
        "",
        "## 3. Pricing opportunities (ranges under stated assumptions)",
        "",
        _md(out.opportunities),
        "",
        *opp_lines,
        "## 4. Experiment design for the top opportunity",
        "",
        f"**{design.title}**",
        "",
        f"- **Hypothesis:** {design.hypothesis}",
        f"- **Unit of randomisation:** {design.unit_of_randomisation}",
        f"- **Primary metric:** {design.primary_metric}",
        "- **Guardrail metrics:** " + "; ".join(design.guardrail_metrics),
        "- **Risks:** " + " ".join(design.risks),
        f"- **Decision rule:** {design.decision_rule}",
        "",
        "### Feasibility and power (SKU-level; statsmodels)",
        "",
        f"Historical planning uses non-overlapping {design.duration_weeks}-week windows and "
        "creates every eligible SKU-week, so weeks with no sale contribute zero. Repeated "
        "weeks are aggregated to one outcome per SKU. The historical mean is GBP "
        f"{out.baseline_mean:,.2f} and the unadjusted between-outcome SD is GBP "
        f"{out.baseline_sd:,.2f}.",
        "",
        f"The pre-period/outcome correlation is {design.preperiod_correlation:.3f}; treating "
        f"that historical relationship as a planning assumption gives a residual SD of GBP "
        f"{out.cuped_residual_sd:,.2f} ({design.variance_reduction:.1%} estimated variance "
        "reduction). This is not an observed experiment result.",
        "",
        f"There are **{design.eligible_products:,} eligible SKUs**, allowing "
        f"**{design.available_products_per_arm:,} per arm**. A {power.mde_relative:.0%} target "
        f"at alpha {power.alpha} and power {power.power} requires "
        f"**{design.required_products_per_arm:,} SKUs per arm**, even after the historical "
        "pre-period adjustment. The proposed 5% test is therefore **not adequately powered**. "
        f"With all eligible SKUs, the adjusted detectable effect is about "
        f"**{design.mde_available_adjusted:.1%}** (unadjusted: "
        f"{design.mde_available_unadjusted:.1%}).",
        "",
        "A smaller pilot may validate assignment, price delivery, zero-sales capture and "
        "cancellation guardrails, but must not be presented as an efficacy test. A full "
        "catalogue test is defensible only if the business pre-registers the larger detectable "
        "effect and accepts the catalogue-wide operational exposure.",
        "",
        "Live sizing workbook (editable formulas): "
        f"`{load_settings()['pricing']['workbook_path']}`.",
        "",
        "## Limitations",
        "",
        "- All price-response figures are associations, not causal effects; the headline "
        "actions are hypotheses with scenario ranges, not promised savings.",
        "- The realisation and leakage gaps assume unchanged volume at higher prices, which is "
        "unlikely to hold fully — the experiment exists precisely to measure the volume response.",
        "- No cost data, so margin is scenario-only. Figures are historical (2010–2011, one UK "
        "retailer) and illustrate method.",
        "- Historical pre-period correlation may not persist prospectively; report both adjusted "
        "and unadjusted estimates and use SKU-level confidence intervals in the readout.",
        "",
    ]
    report = "\n".join(lines)
    _assert_no_causal_elasticity(report)
    return report


def _assert_no_causal_elasticity(report: str) -> None:
    low = report.lower()
    for term in FORBIDDEN_IN_DESCRIPTIVE:
        # Allowed only in a negated disclaimer ("not a price elasticity", "no price elasticity").
        idx = low.find(term)
        while idx != -1:
            # Strip markdown so "**not**" reads as "not"; look for a negation nearby.
            prefix = low[max(0, idx - 30):idx].replace("*", " ")
            if not any(neg in prefix for neg in ("not ", "no ", "never")):
                raise AssertionError(f"Report asserts '{term}' without a non-causal disclaimer.")
            idx = low.find(term, idx + 1)
