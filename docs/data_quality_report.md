# Data-quality report — M1 (ingest, clean, model)

_Generated 2026-11-16 from the DuckDB warehouse. Every figure is produced by the pipeline; do not edit by hand._

## Source

- **Dataset:** UCI Online Retail II (CC BY 4.0). Chen, D. (2019). Online Retail II [Dataset]. UCI Machine Learning Repository. <https://doi.org/10.24432/C5CG6D>.
- **Transactions kept:** 1,033,062 lines, 2009-12-01 to 2011-12-09.
- **Customers (identified):** 5,875. **Products:** 4,739.
- **Currency:** GBP. Revenue excludes postage, fees and adjustments (rule R04).

## Reconciliation

**Raw value = removed value + kept net revenue**, to a tenth of a penny. Sums use exact DECIMAL arithmetic, so there is no rounding tolerance.

| Metric | Value (GBP / rows) |
| --- | --- |
| Raw rows (staged) | 1,067,371 |
| Rows removed | 34,309 |
| Rows kept | 1,033,062 |
| Gross product revenue | 19,700,954.46 |
| Cancellations | -719,692.94 |
| Net product revenue | 18,981,261.52 |
| Row difference (must be 0) | 0 |
| Value difference (must be 0) | 0.0000 |

**Reconciled:** yes.

## Rows removed by rule

Each removed row is counted against the first rule it breaks, so these rows sum to *rows removed* above. Rule definitions: [data_cleaning_rules.md](data_cleaning_rules.md).

| Rule | Name | Rows removed | Units removed | Value removed (GBP) |
| --- | --- | --- | --- | --- |
| R01_sheet_overlap | Sheet overlap | 22,523 | 166,648 | 377488.450 |
| R03_missing_key_field | Missing key field | 0 | 0 | 0.000 |
| R04_non_product_code | Non-product code | 5,813 | 10,421 | -71499.399 |
| R05_zero_price | Zero price | 5,973 | -320,652 | 0.000 |
| R06_negative_price | Negative price | 0 | 0 | 0.000 |
| R07_nonpositive_qty_on_sale | Non-positive quantity on a sales invoice | 0 | 0 | 0.000 |
| R08_nonnegative_qty_on_cancellation | Non-negative quantity on a cancellation | 0 | 0 | 0.000 |

## Known issues kept in the data

These are not removed; analyses downstream must account for them.

| Check | Description | Rows / count | Value (GBP) | % of net revenue |
| --- | --- | --- | --- | --- |
| F01_missing_customer | Kept lines without a customer ID | 227,214 | 2569366.770 | 13.54 |
| F02_extreme_line | Kept lines at or above the extreme quantity/value thresholds | 46 | 123890.370 | 0.65 |
| F03_duplicate_looking_line | Exact-looking repeat lines retained because source line identity is unavailable | 11,790 | 53862.450 | 0.28 |
| I01_multi_description_products | Products whose stock code carries more than one description (count of products) | 596 |  |  |
| I02_code_case_variants | Products whose stock code appears in more than one letter case (count of products) | 170 |  |  |
| I03_multi_timestamp_invoices | Kept invoices with lines at more than one timestamp (count of invoices) | 83 |  |  |
| I04_partial_months | Calendar months only partly covered by the data (count of months) | 1 |  |  |
| I05_left_censored_customers | Customers whose first purchase is in the first month of data (count of customers) | 951 |  |  |
| I06_cancellation_only_customers | Customers with cancellations but no kept sale line (count of customers) | 23 |  |  |

## Sheet-overlap verification (rule R01)

The workbook's two sheets overlap for 1–9 Dec 2010. R01 drops the earlier copy only after checking it matches the later sheet row-for-row. `unmatched_rows` must be 0.

| overlap_rows_dropped | matching_window_rows_kept | unmatched_rows |
| --- | --- | --- |
| 22,523 | 22,523 | 0 |

## Exact-looking line sensitivity

The workbook has no immutable source-line identifier. Exact-looking repeated lines are therefore retained and flagged rather than silently deleted. The alternative exclusion scenario below shows the uncertainty; proven sheet overlap is removed in both scenarios.

| duplicate_policy | fact_lines | sale_units | cancellation_units | gross_revenue | cancellations | net_revenue | sale_invoices | cancellation_invoices | all_invoices | gross_sales_aov |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| retain_ambiguous | 1,033,062 | 11,221,957 | -469,882 | 19700954.457 | -719692.940 | 18981261.517 | 39,516 | 7,406 | 46,922 | 498.56 |
| exclude_repeat_lookalikes | 1,021,272 | 11,188,061 | -467,740 | 19643861.637 | -716462.570 | 18927399.067 | 39,516 | 7,406 | 46,922 | 497.11 |
