# M3 — Customer intelligence (findings)

_Generated 2026-11-16 from the DuckDB warehouse. Every figure is computed by `commercial_intelligence.customers`; do not edit by hand._

Scope: identified customers only (guests, ~1/5 of revenue, carry no customer id and are excluded from this milestone). Activity = sales; returns are excluded from purchase counts.

## Headline

- **5,852 identified customers** segmented by RFM and k-means.
- **Month-1 repeat rate ≈ 21%** — most first-time buyers do not return the next month; retention then flattens (see heatmap).
- The BG/NBD + Gamma-Gamma model does **not** beat the historical-value baseline on complete held-out customer value (MAE GBP 644.46 vs 633.45). Per the integrity rules, forward scores use the simpler baseline.

## 1. Segmentation

### RFM business segments

Recency / Frequency / Monetary scored into quintiles and mapped to the classic segment grid.

| rfm_segment | customers | monetary_gbp |
| --- | --- | --- |
| Champions | 1564 | 11,755,846.00 |
| Loyal customers | 574 | 1,850,908.00 |
| At risk | 313 | 887,112.00 |
| Lost / inactive | 1209 | 439,205.00 |
| Potential loyalist | 683 | 410,238.00 |
| Hibernating | 691 | 370,495.00 |
| Can't lose them | 128 | 355,837.00 |
| Promising / need attention | 596 | 328,612.00 |
| New customers | 94 | 15,048.00 |

### k-means on scaled RFM

Features: recency, log(frequency), log(monetary), standardised. k chosen by silhouette over [3, 4, 5, 6]: **k = 3** (silhouette 0.399). Silhouette by k: 3:0.399, 4:0.360, 5:0.360, 6:0.342.

**Stability:** fitting RFM k-means independently on two time windows and comparing by Adjusted Rand Index gives ARI = **0.167** on 2,704 customers active in both windows. A modest ARI means cluster *membership* shifts as customers' behaviour changes, even though the cluster *shapes* are stable — so the simple, transparent RFM grid is the recommended operational segmentation, with k-means as a cross-check.

| cluster | customers | recency_days | frequency | median_monetary_gbp | total_monetary |
| --- | --- | --- | --- | --- | --- |
| 2 | 1642 | 24 | 11 | 3,853 | 13,432,040 |
| 0 | 2374 | 60 | 3 | 715 | 2,022,066 |
| 1 | 1836 | 436 | 1 | 317 | 959,195 |

## 2. Cohort retention

Monthly cohorts by first-purchase month. Average retention by months-since-acquisition (cohorts old enough to be observed):

| month_offset | avg_retention_share | cohorts |
| --- | --- | --- |
| 0 | 1.000 | 25 |
| 1 | 0.210 | 24 |
| 2 | 0.219 | 23 |
| 3 | 0.217 | 22 |
| 4 | 0.206 | 21 |
| 5 | 0.189 | 20 |
| 6 | 0.179 | 19 |
| 7 | 0.178 | 18 |
| 8 | 0.157 | 17 |
| 9 | 0.153 | 16 |
| 10 | 0.151 | 15 |
| 11 | 0.165 | 14 |
| 12 | 0.183 | 13 |

Heatmap: `assets/customers/cohort_retention.png`.

## 3. Customer value — honest evaluation

**Time-based holdout (no leakage):** calibrate on transactions up to 2011-05-31, test on the following 192 days (2011-12-09). 4,908 customers acquired during calibration are scored; features never see the holdout.

Predicted vs actual **complete holdout customer value (GBP)**. This is the selection metric because it evaluates purchase frequency and monetary value together:

| method | MAE | RMSE | pred_total | actual_total |
| --- | --- | --- | --- | --- |
| BG/NBD + Gamma-Gamma | 644.455 | 3,576.269 | 4,046,102.131 | 4,709,097.861 |
| Baseline (historical avg value) | 633.453 | 3,434.078 | 4,183,927.517 | 4,709,097.861 |

Winner on MAE: **Baseline (historical avg value)**.

Purchase-count diagnostics (not used alone to select CLV):

| method | MAE | RMSE | pred_total | actual_total |
| --- | --- | --- | --- | --- |
| BG/NBD | 1.089 | 1.859 | 8,051.673 | 8,092.000 |
| Baseline (historical avg) | 1.139 | 2.086 | 8,495.313 | 8,092.000 |

**Monetary (Gamma-Gamma) check:** predicted average order value vs actual holdout AOV on 2,157 repeat customers — Gamma-Gamma MAE GBP 163.97 vs naive (calibration AOV) MAE GBP 163.68.

Calibration plot: `assets/customers/clv_calibration.png`. Forward CLV scores per customer: `data/exports/customers/clv_customers.parquet`.

**Robustness.** Re-running complete-value evaluation at several calibration cut-offs shows whether the selected method is stable across time:

| calibration_end | holdout_days | customers | model value MAE | baseline value MAE | model_wins |
| --- | --- | --- | --- | --- | --- |
| 2011-03-31 | 253 | 4691 | 777.288 | 740.578 | False |
| 2011-05-31 | 192 | 4908 | 644.455 | 633.453 | False |
| 2011-07-31 | 131 | 5117 | 502.660 | 495.148 | False |

## Limitations

- CLV and segments cover identified customers only; guest revenue (~20%) is out of scope here and shown in the revenue bridges (M2) instead.
- **RFM quintiles and tied values:** about 28% of customers have bought only once, so the Frequency quintile boundary falls inside a large tie. Those single-purchase customers are split between the lowest two F-scores by a deterministic but arbitrary tie-break; the F-score is therefore coarse at the low end. The k-means view, which uses the raw values, does not have this boundary effect.
- **Cohort right-censoring:** later month-offsets are averaged over only the earlier cohorts old enough to reach them (offset 12 uses 13 of 25 cohorts), so the small late-tenure uptick is a cohort-composition effect, not a genuine recovery in loyalty.
- BG/NBD assumes a non-contractual, steady-purchasing process; promotions and the catalogue churn seen in M2 violate this, so treat CLV as a ranking aid, not a guaranteed forecast. The horizon value is undiscounted.
- The selected historical-value baseline forecasts future repeat value only. Customers with no observed repeat purchase receive a conservative zero forward score; this is not their total lifetime revenue and never subtracts prior purchases.
- Only ~24 months of data: the holdout is a single 6-month window, so the evaluation shows relative model quality, not long-run accuracy.
- Figures are historical (2010–2011, one UK retailer) and illustrate method.
