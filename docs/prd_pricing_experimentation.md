# PRD — Pricing experimentation capability

## Problem

The commercial team can see *where* revenue moves and can measure pricing *associations*, but cannot establish *causal* price effects. Pricing decisions are currently made on observational signals (dispersion, realisation gaps) that confound demand with quantity-break and customer mix. The business needs a repeatable way to test price changes safely and read the result.

## Users

- **Pricing manager** — designs and reads price tests.
- **Commercial director** — approves and acts on results.
- **Category manager** — nominates candidate products.
- **Analytics** — owns randomisation, metrics and the readout.

## Requirements

- Define a candidate set (e.g. high-dispersion products) and randomise at the **SKU** level, stratified by family and revenue decile.
- Apply a treatment (e.g. a price floor) to the treatment arm only; hold control unchanged.
- Aggregate repeated weeks to one **SKU-level primary outcome** (average weekly gross sales revenue, including zero-sales weeks) and track units, sale invoices and cancellations as guardrails.
- Pre-register the hypothesis, minimum detectable effect, sample size and decision rule before launch.
- Provide a power calculator (the live Excel workbook) and an automated readout.

## Metrics

- **Primary:** average weekly gross sales revenue per SKU. A 5% target requires ~21,102 SKUs per arm, but only 1,713 are available; adjusted MDE is about 17.6% over 8 weeks.
- **Guardrails:** units/SKU-week, sale invoices/SKU-week, cancellation value/rate.
- **Decision:** estimate intention-to-treat with SKU-level ANCOVA; require a two-sided p-value below alpha, a confidence interval excluding zero, and no pre-registered guardrail breach.

## Risks

- **Contamination** (substitution between treated/control products) — randomise whole sub-categories where substitution is high.
- **Novelty / seasonality** — run whole weeks; block on calendar period (strong Q4 peak in the data).
- **Operational** — price floors must be reversible and clearly governed.

## Rollout

1. Pilot assignment, price delivery and telemetry on one family's products; do not use that pilot to claim efficacy.
2. Pre-register and run the SKU-randomised test only for an effect size the available catalogue can detect.
3. Read out against primary + guardrails; ship, iterate or stop per the decision rule.
4. Templatise so new price hypotheses reuse the same randomisation and readout.
