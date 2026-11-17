# M5 — Pricing opportunities and experiment design (findings)

_Generated 2026-11-16 by `commercial_intelligence.pricing`._

> **Non-causal.** Every price-quantity relationship here is a descriptive **association** from observational data. No price elasticity is estimated and no number states the revenue effect of a deliberate price change. Revenue opportunities are **scenario ranges under stated assumptions**, not forecasts. Margin figures are a labelled scenario only — there is no cost data. A causal effect can be established only by the randomised experiment specified below.

## 1. Price dispersion

Of 3,460 products with enough sale history, **99.0%** are sold at more than one unit price (median within-product price coefficient of variation 0.35). This dispersion is the raw material for the opportunities below. Full table: `data/exports/pricing/price_dispersion_products.csv`.

## 2. Descriptive price–quantity association by family

Log-log association between unit price and quantity, by family. The **within-product** slope uses only price variation for the *same product over time* (product fixed effects); it is the more comparable figure but remains an **association**, confounded by quantity-break pricing, seasonality and customer mix. It is **not** a price elasticity.

| family_code | family | n_lines | n_products | pooled_slope | within_slope | within_ci_low | within_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SC | Stationery & Craft | 60660 | 257 | -0.786 | -1.853 | -1.884 | -1.821 |
| OT | Other / Unsure | 9641 | 23 | -0.876 | -1.748 | -1.827 | -1.670 |
| CL | Candles & Lighting | 49432 | 245 | -0.792 | -1.664 | -1.696 | -1.632 |
| TG | Toys & Games | 37727 | 182 | -0.618 | -1.606 | -1.642 | -1.569 |
| SP | Signs & Plaques | 56023 | 173 | -0.566 | -1.545 | -1.570 | -1.520 |
| GO | Garden & Outdoor | 13524 | 53 | -0.542 | -1.532 | -1.597 | -1.467 |
| FA | Fashion & Accessories | 17834 | 100 | -0.552 | -1.519 | -1.559 | -1.478 |
| BG | Bags & Luggage | 100727 | 257 | -0.752 | -1.465 | -1.489 | -1.442 |
| PC | Party & Celebration | 51004 | 197 | -0.470 | -1.427 | -1.455 | -1.398 |
| KD | Kitchen & Dining | 296297 | 1431 | -0.553 | -1.425 | -1.436 | -1.414 |
| HD | Home Decor & Ornaments | 240411 | 1486 | -0.537 | -1.406 | -1.420 | -1.392 |
| XM | Christmas & Seasonal | 42006 | 178 | -0.556 | -1.177 | -1.204 | -1.149 |
| TX | Textiles & Soft Furnishings | 39763 | 142 | -0.509 | -1.109 | -1.141 | -1.076 |

Negative slopes mean larger quantities are associated with lower unit prices — consistent with bulk discounting, which is a confounder, not a demand response.

## 3. Pricing opportunities (ranges under stated assumptions)

| key | name | measured_gap_gbp | impact_low_gbp | impact_high_gbp | impact_low_pct_rev | impact_high_pct_rev | margin_scenario_low_gbp | margin_scenario_high_gbp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| price_realization | Price realisation on high-dispersion products | 2,327,994.00 | 465,599.00 | 1,163,997.00 | 2.45 | 6.13 | 209,519.00 | 523,799.00 |
| discount_leakage | Quantity-break redesign (discount leakage on small-quantity lines) | 4,371.00 | 874.00 | 2,185.00 | 0.00 | 0.01 | 393.00 | 983.00 |

### Price realisation on high-dispersion products

- **Observation (descriptive):** 3,147 products (≥30 sale lines) are sold below their own median unit price often enough to leave a measured price-realisation gap of GBP 2,327,994 at unchanged volume.
- **Hypothesis (action):** Tightening how far below the median list price these products can be sold (price-floor / discount governance) is associated with higher revenue.
- **Scenario revenue range:** GBP 465,599 – 1,163,997 (2.45%–6.13% of net revenue), under the assumptions below.
- **Margin scenario (assumed cost ratio, illustrative only):** GBP 209,519 – 523,799.
- **Assumptions:** (1) Only 20–50% of the measured gap is recoverable (partial realisation). (2) Volume is held constant — a strong assumption; higher prices may reduce units. (3) Reference price = each product's own median; extreme-flagged lines excluded.
- **Confounders / caveats:** Below-median prices may reflect genuine quantity-break deals, clearance, or key-account pricing, not leakage.
- **Validation:** causal effect unknown until tested by the experiment below.

### Quantity-break redesign (discount leakage on small-quantity lines)

- **Observation (descriptive):** Small-quantity lines (below a product's median line quantity) are sometimes sold at deep discounts (below the product's 25th price percentile), a measured gap of GBP 4,371 versus the median price.
- **Hypothesis (action):** Restricting deep discounts to genuinely large line quantities (a redesigned quantity-break schedule) is associated with higher revenue on small-quantity lines.
- **Scenario revenue range:** GBP 874 – 2,185 (0.00%–0.01% of net revenue), under the assumptions below.
- **Margin scenario (assumed cost ratio, illustrative only):** GBP 393 – 983.
- **Assumptions:** (1) Only 20–50% of the leakage gap is recoverable. (2) Small-quantity discounted lines would still convert at the median price (uncertain).
- **Confounders / caveats:** Some small-quantity discounted lines are samples, staff sales or loyalty gestures.
- **Validation:** causal effect unknown until tested by the experiment below.

## 4. Experiment design for the top opportunity

**Price-realisation floor on high-dispersion products**

- **Hypothesis:** Introducing a price floor (limiting how far below the median list price a product may be sold) raises average weekly gross sales revenue per SKU without a material fall in units. This is a causal hypothesis to be tested: the observational analysis establishes only an association, and this randomised test is what would confirm an effect.
- **Unit of randomisation:** Product (SKU). Candidate high-dispersion products are randomised to a treatment arm (price floor applied) or a control arm (unchanged), stratified by family and revenue decile.
- **Primary metric:** Average weekly gross sales revenue per assigned SKU over 8 weeks, including zero-sales weeks. Analyse one outcome per SKU with pre-period revenue and randomisation strata as covariates.
- **Guardrail metrics:** Units sold per SKU-week (including zeros; volume must not fall materially).; Sale-invoice count per SKU-week.; Cancellation value and cancellation-invoice rate.
- **Risks:** Contamination: customers substitute between treated and control products (mitigate by randomising whole sub-categories where substitution is high). Novelty / promotion-timing effects: run across whole weeks, avoid launch spikes. Repeated weeks within a SKU are not independent; aggregate the full test window to one SKU outcome and use the SKU as the analysis unit. Seasonality: run treatment and control concurrently across whole weeks.
- **Decision rule:** Estimate the intention-to-treat effect with SKU-level ANCOVA. Claim a positive effect only if the two-sided p-value is below 0.05, the confidence interval excludes zero, and no pre-registered guardrail is breached. Do not use the observational scenario range as the success threshold.

### Feasibility and power (SKU-level; statsmodels)

Historical planning uses non-overlapping 8-week windows and creates every eligible SKU-week, so weeks with no sale contribute zero. Repeated weeks are aggregated to one outcome per SKU. The historical mean is GBP 52.81 and the unadjusted between-outcome SD is GBP 153.23.

The pre-period/outcome correlation is 0.775; treating that historical relationship as a planning assumption gives a residual SD of GBP 96.81 (60.1% estimated variance reduction). This is not an observed experiment result.

There are **3,427 eligible SKUs**, allowing **1,713 per arm**. A 5% target at alpha 0.05 and power 0.8 requires **21,102 SKUs per arm**, even after the historical pre-period adjustment. The proposed 5% test is therefore **not adequately powered**. With all eligible SKUs, the adjusted detectable effect is about **17.6%** (unadjusted: 27.8%).

A smaller pilot may validate assignment, price delivery, zero-sales capture and cancellation guardrails, but must not be presented as an efficacy test. A full catalogue test is defensible only if the business pre-registers the larger detectable effect and accepts the catalogue-wide operational exposure.

Live sizing workbook (editable formulas): `excel/experiment_sizing.xlsx`.

## Limitations

- All price-response figures are associations, not causal effects; the headline actions are hypotheses with scenario ranges, not promised savings.
- The realisation and leakage gaps assume unchanged volume at higher prices, which is unlikely to hold fully — the experiment exists precisely to measure the volume response.
- No cost data, so margin is scenario-only. Figures are historical (2010–2011, one UK retailer) and illustrate method.
- Historical pre-period correlation may not persist prospectively; report both adjusted and unadjusted estimates and use SKU-level confidence intervals in the readout.
