"""Templated commercial memo, KPI tree and PRD.

Every number is pulled from the validated exports via `memo_numbers()` and
formatted through the shared helpers, so nothing is hand-typed. A test
recomputes the key figures from the exports and asserts they appear verbatim in
the rendered memo.
"""

from __future__ import annotations

from datetime import date

from commercial_intelligence.reporting import exports


def _gbp(v: float) -> str:
    return f"−£{abs(v):,.0f}" if v < 0 else f"£{v:,.0f}"


def _gbpm(v: float) -> str:
    return f"£{v / 1e6:.2f}m"


def _pct(v: float, dp: int = 1) -> str:
    return f"{v:+.{dp}f}%" if v < 0 or v > 0 else f"{v:.{dp}f}%"


def memo_numbers() -> dict:
    """All figures the memo/KPI-tree/PRD use, sourced from the exports."""
    k = exports.headline_kpis()
    monthly = exports.monthly_revenue()
    gross = float(monthly["gross_revenue"].sum())
    cancellations = float(monthly["cancellations"].sum())

    prod = exports.bridge("product")
    cust = exports.bridge("customer")

    def comp(df, name):
        hit = df.loc[df["component"] == name, "value_gbp"]
        return float(hit.iloc[0]) if len(hit) else 0.0

    clv = exports.clv_metrics().set_index("method")["mae"]
    clv_model = float(clv["BG/NBD + Gamma-Gamma"])
    clv_base = float(clv["Baseline (historical avg value)"])
    clv_winner = "BG/NBD + Gamma-Gamma" if clv_model < clv_base else "Baseline"

    pm = exports.product_metrics().set_index("method")["macro_f1"]
    base_f1 = float(pm.get("Baseline (TF-IDF + LogReg)", 0.0))

    opp = exports.opportunities()
    realis = opp.iloc[0]
    exp = exports.experiment_summary().iloc[0]
    curve = exports.retention_curve()
    month1 = float(curve.loc[curve["month_offset"] == 1, "avg_retention"].iloc[0])

    return {
        "net_revenue": k["net_revenue"],
        "gross_revenue": gross,
        "cancellations": cancellations,
        "sale_invoices": k["sale_invoices"],
        "cancellation_invoices": k["cancellation_invoices"],
        "all_invoices": k["all_invoices"],
        "gross_sales_aov": k["gross_sales_aov"],
        "active_customers": k["active_customers"],
        "units_sold": k["units_sold"],
        "avg_unit_price": gross / k["units_sold"],
        "sale_invoices_per_customer": k["sale_invoices"] / k["active_customers"],
        "repeat_rate": k["repeat_rate"],
        "yoy_pct": k["yoy_pct"],
        "yoy_label": k["yoy_label"],
        "b_price": comp(prod, "Price"),
        "b_volume": comp(prod, "Volume"),
        "b_mix": comp(prod, "Mix"),
        "b_new": comp(prod, "New products"),
        "b_disc": comp(prod, "Discontinued products"),
        "b_new_cust": comp(cust, "New customers"),
        "b_lost_cust": comp(cust, "Lost customers"),
        "b_retained": comp(cust, "Retained customers"),
        "clv_model_mae": clv_model,
        "clv_base_mae": clv_base,
        "clv_wins": clv_model < clv_base,
        "clv_winner": clv_winner,
        "base_f1": base_f1,
        "month1_retention": month1,
        "opp_name": realis["name"],
        "opp_gap": float(realis["measured_gap_gbp"]),
        "opp_low": float(realis["impact_low_gbp"]),
        "opp_high": float(realis["impact_high_gbp"]),
        "opp_low_pct": float(realis["impact_low_pct_rev"]),
        "opp_high_pct": float(realis["impact_high_pct_rev"]),
        "exp_required_per_arm": int(exp["required_products_per_arm"]),
        "exp_available_per_arm": int(exp["available_products_per_arm"]),
        "exp_target_mde": float(exp["target_mde_relative"]),
        "exp_available_mde": float(exp["mde_available_relative"]),
        "exp_powered": bool(exp["adequately_powered"]),
        "exp_duration": int(exp["duration_weeks"]),
    }


def executive_summary() -> dict:
    """Structured, evidence-linked recommendations for the app's Executive page.

    Built from the same templated numbers as the memo, so the app shows no
    hand-typed business results.
    """
    n = memo_numbers()
    recommendations = [
        {
            "priority": 1,
            "action": "Run a price-floor experiment on high-dispersion products",
            "evidence": (
                f"A measured price-realisation gap of {_gbp(n['opp_gap'])}; most products "
                "sell at several unit prices."
            ),
            "scenario_impact": f"{_gbp(n['opp_low'])} – {_gbp(n['opp_high'])} (scenario range)",
            "success_metric": (
                "Positive SKU-level ANCOVA estimate with confidence interval above zero; "
                "volume and cancellation guardrails held."
            ),
            "confidence": "Medium — association only; the experiment establishes causality.",
        },
        {
            "priority": 2,
            "action": "Shift investment toward first-90-day retention",
            "evidence": (
                f"About {n['month1_retention']*100:.0f}% of first-time buyers return the next "
                f"month; retained customers spent {_gbp(n['b_retained'])} year on year."
            ),
            "scenario_impact": "Not sized — diagnostic; frame as a retention test.",
            "success_metric": "Lift in the 90-day repeat rate of acquired cohorts.",
            "confidence": "Medium — cohort evidence is descriptive.",
        },
        {
            "priority": 3,
            "action": (
                "Use modelled customer value to prioritise retention spend"
                if n["clv_wins"]
                else "Use the historical-value baseline for customer prioritisation"
            ),
            "evidence": (
                f"Complete held-out value MAE is GBP {n['clv_model_mae']:,.2f} for the "
                f"model and GBP {n['clv_base_mae']:,.2f} for the baseline; "
                f"{n['clv_winner']} is selected."
            ),
            "scenario_impact": "Targeting aid, not a revenue forecast.",
            "success_metric": "Higher return on retention spend in a prospective test.",
            "confidence": "Medium — selected on complete held-out customer value.",
        },
    ]
    monitoring = [
        {"name": "Net revenue", "definition": "Product revenue, sales minus returns (GBP)."},
        {"name": "90-day repeat rate",
         "definition": "Share of a cohort buying again within 90 days."},
        {"name": "Gross sales AOV",
         "definition": "Gross product sales revenue ÷ distinct sale invoices."},
        {"name": "Price realisation",
         "definition": "Share of the dispersion gap recovered on treated products."},
        {"name": "Units (guardrail)",
         "definition": "Volume on treated products must not fall materially."},
        {"name": "Return rate", "definition": "Cancellations as a share of gross revenue."},
    ]
    limitations = [
        "No cost data, so margin appears only as a labelled scenario, never a realised figure.",
        "Pricing and retention findings are associations; a causal effect needs the experiment.",
        "Data is historical (2010–2011, one UK retailer); ~20% of revenue has no customer id.",
    ]
    situation = (
        f"Net product revenue totals {_gbpm(n['net_revenue'])}; gross sales span "
        f"{n['sale_invoices']:,.0f} sale invoices at a gross sales AOV of "
        f"{_gbp(n['gross_sales_aov'])}, with {n['cancellation_invoices']:,.0f} cancellation "
        f"invoices retained in net revenue. Over the comparison window "
        f"({n['yoy_label']}) it moved {_pct(n['yoy_pct'])}, carried by new products "
        f"({_gbp(n['b_new'])}) while the continuing range lost volume ({_gbp(n['b_volume'])}) and "
        f"retained customers spent less ({_gbp(n['b_retained'])}). The clearest structural gap is "
        f"retention: about {n['month1_retention']*100:.0f}% of first-time buyers return next month."
    )
    return {
        "situation": situation,
        "headline": {
            "net_revenue": n["net_revenue"],
            "sale_invoices": int(n["sale_invoices"]),
            "cancellation_invoices": int(n["cancellation_invoices"]),
            "gross_sales_aov": n["gross_sales_aov"],
            "active_customers": int(n["active_customers"]),
            "yoy_pct": n["yoy_pct"],
            "yoy_label": n["yoy_label"],
        },
        "recommendations": recommendations,
        "monitoring_kpis": monitoring,
        "limitations": limitations,
    }


def render_memo(n: dict) -> str:
    lines = [
        "# Commercial performance memo",
        "",
        f"_{date.today().isoformat()} · Audience: commercial director, pricing manager, "
        "CRM and category managers. Every figure is generated from the analytics "
        "pipeline._",
        "",
        "## Answer first",
        "",
        f"Net revenue over the comparable window ({n['yoy_label']}) is **{_pct(n['yoy_pct'])}** "
        f"year-on-year. The headline is healthy but the *composition* is the concern: growth "
        f"is carried by **new products ({_gbp(n['b_new'])})** while the continuing range lost "
        f"volume (**{_gbp(n['b_volume'])}**), and **retained customers spent less "
        f"({_gbp(n['b_retained'])})**. The business is refreshing its catalogue and customer "
        f"base rather than deepening either. Total net revenue is **{_gbpm(n['net_revenue'])}** "
        f"from **{n['sale_invoices']:,.0f} sale invoices** at a gross sales AOV of "
        f"**{_gbp(n['gross_sales_aov'])}**; **{n['cancellation_invoices']:,.0f} cancellation "
        "invoices** remain in net revenue.",
        "",
        "## What moved revenue",
        "",
        f"- **Product price/volume/mix:** price {_gbp(n['b_price'])}, "
        f"volume {_gbp(n['b_volume'])}, "
        f"mix {_gbp(n['b_mix'])}; new products {_gbp(n['b_new'])}, discontinued "
        f"{_gbp(n['b_disc'])}. (Descriptive attribution, not a causal price effect.)",
        f"- **Customers:** new {_gbp(n['b_new_cust'])}, lost {_gbp(n['b_lost_cust'])}, retained "
        f"{_gbp(n['b_retained'])}. About **{n['month1_retention']*100:.0f}%** of first-time "
        "buyers return the next month — retention, not acquisition, is the gap.",
        "",
        "## Recommendations (impact as ranges, under stated assumptions)",
        "",
        f"1. **{n['opp_name']}.** A measured price-realisation gap of {_gbp(n['opp_gap'])} "
        f"supports a scenario uplift of **{_gbp(n['opp_low'])}–{_gbp(n['opp_high'])}** "
        f"({n['opp_low_pct']:.1f}–{n['opp_high_pct']:.1f}% of net revenue) if partially "
        "recovered without volume loss. Validate with the experiment below before acting.",
        "2. **Shift investment toward first-90-day retention.** Repeat purchasing is weak; a "
        "retention programme targets the clearest structural gap. Frame as a measured test.",
        "3. **Redesign quantity-break discounts** to stop deep discounts leaking to small "
        "line quantities (a smaller but clean governance win).",
        f"4. **Use the selected customer-value approach for ranking only.** Complete held-out "
        f"value MAE is GBP {n['clv_model_mae']:,.2f} for BG/NBD + Gamma-Gamma versus GBP "
        f"{n['clv_base_mae']:,.2f} for the historical-value baseline; "
        f"**{n['clv_winner']}** is selected.",
        f"5. **Adopt the validated TF-IDF product taxonomy** (held-out macro-F1 "
        f"{n['base_f1']:.3f}). The former LLM score was withdrawn because its replay "
        "labels were not independent of the gold set.",
        "",
        "## What we do NOT know",
        "",
        "- **No cost data → no margin.** Every margin figure elsewhere is a labelled scenario.",
        "- **No causality.** Price and retention findings are *associations*; the proposed "
        "experiment is required before claiming any uplift.",
        "- **Data age & scope.** 2009–2011, one UK retailer — illustrates method, not current "
        "market facts. ~20% of revenue has no customer id.",
        "",
        "## Next steps",
        "",
        f"The SKU-randomised price-floor design is **not powered for its "
        f"{n['exp_target_mde']:.0%} target**: it requires "
        f"**{n['exp_required_per_arm']:,} SKUs per arm**, versus "
        f"**{n['exp_available_per_arm']:,} available** over {n['exp_duration']} weeks. Even "
        f"with the historical pre-period adjustment, the available catalogue detects about "
        f"**{n['exp_available_mde']:.1%}**. Use a smaller pilot only for operational validation, "
        "not an uplift claim.",
        "",
    ]
    return "\n".join(lines)


def render_kpi_tree(n: dict) -> str:
    return "\n".join([
        "# KPI tree",
        "",
        "_Values generated from the pipeline. Two revenue identities; figures tie out._",
        "",
        "```",
        f"Net revenue  {_gbpm(n['net_revenue'])}",
        "├─ Gross sales:  Sale invoices × gross sales AOV",
        f"│   ├─ Sale invoices          {n['sale_invoices']:,.0f}",
        f"│   │   ├─ Active customers   {n['active_customers']:,.0f}",
        f"│   │   └─ Sales / customer   {n['sale_invoices_per_customer']:.1f}",
        f"│   └─ Gross sales AOV        {_gbp(n['gross_sales_aov'])}",
        f"├─ Cancellations              {_gbp(n['cancellations'])}",
        "└─ via units (gross):   Units × Avg unit price",
        f"    ├─ Units sold            {n['units_sold']:,.0f}",
        f"    └─ Avg unit price        £{n['avg_unit_price']:.2f}",
        "```",
        "",
        "- Gross sales → **sale invoices × gross sales AOV**; cancellations are then added "
        "to reconcile to net revenue.",
        "- Gross revenue → **units × average unit price** (gross of returns).",
        f"- Repeat rate (identified customers with ≥2 sale invoices): "
        f"**{n['repeat_rate']*100:.0f}%**.",
        "",
    ])


def render_prd(n: dict) -> str:
    return "\n".join([
        "# PRD — Pricing experimentation capability",
        "",
        "## Problem",
        "",
        "The commercial team can see *where* revenue moves and can measure pricing "
        "*associations*, but cannot establish *causal* price effects. Pricing decisions are "
        "currently made on observational signals (dispersion, realisation gaps) that confound "
        "demand with quantity-break and customer mix. The business needs a repeatable way to "
        "test price changes safely and read the result.",
        "",
        "## Users",
        "",
        "- **Pricing manager** — designs and reads price tests.",
        "- **Commercial director** — approves and acts on results.",
        "- **Category manager** — nominates candidate products.",
        "- **Analytics** — owns randomisation, metrics and the readout.",
        "",
        "## Requirements",
        "",
        "- Define a candidate set (e.g. high-dispersion products) and randomise at the **SKU** "
        "level, stratified by family and revenue decile.",
        "- Apply a treatment (e.g. a price floor) to the treatment arm only; hold control "
        "unchanged.",
        "- Aggregate repeated weeks to one **SKU-level primary outcome** (average weekly gross "
        "sales revenue, including zero-sales weeks) and track units, sale invoices and "
        "cancellations as guardrails.",
        "- Pre-register the hypothesis, minimum detectable effect, sample size and decision "
        "rule before launch.",
        "- Provide a power calculator (the live Excel workbook) and an automated readout.",
        "",
        "## Metrics",
        "",
        f"- **Primary:** average weekly gross sales revenue per SKU. A "
        f"{n['exp_target_mde']:.0%} target requires ~{n['exp_required_per_arm']:,} SKUs per "
        f"arm, but only {n['exp_available_per_arm']:,} are available; adjusted MDE is about "
        f"{n['exp_available_mde']:.1%} over {n['exp_duration']} weeks.",
        "- **Guardrails:** units/SKU-week, sale invoices/SKU-week, cancellation value/rate.",
        "- **Decision:** estimate intention-to-treat with SKU-level ANCOVA; require a "
        "two-sided p-value below alpha, a confidence interval excluding zero, and no "
        "pre-registered guardrail breach.",
        "",
        "## Risks",
        "",
        "- **Contamination** (substitution between treated/control products) — randomise whole "
        "sub-categories where substitution is high.",
        "- **Novelty / seasonality** — run whole weeks; block on calendar period (strong Q4 "
        "peak in the data).",
        "- **Operational** — price floors must be reversible and clearly governed.",
        "",
        "## Rollout",
        "",
        "1. Pilot assignment, price delivery and telemetry on one family's products; do not "
        "use that pilot to claim efficacy.",
        "2. Pre-register and run the SKU-randomised test only for an effect size the available "
        "catalogue can detect.",
        "3. Read out against primary + guardrails; ship, iterate or stop per the decision rule.",
        "4. Templatise so new price hypotheses reuse the same randomisation and readout.",
        "",
    ])
