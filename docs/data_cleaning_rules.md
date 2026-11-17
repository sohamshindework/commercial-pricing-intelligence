# Data cleaning rules (M1)

Each rule is applied in order. A removed row is attributed to the **first** rule
it breaks, so the counts in [`data_quality_report.md`](data_quality_report.md)
sum exactly to the rows removed. Rules live in
[`sql/seeds/cleaning_rules.csv`](../sql/seeds/cleaning_rules.csv); the logic is in
[`sql/intermediate/int_transactions_flagged.sql`](../sql/intermediate/int_transactions_flagged.sql).

## Revenue definition

Net product revenue = Σ `quantity × unit_price` in GBP over kept lines, where a
`sale` line has positive quantity and a `cancellation` line (invoice starting
`C`) has negative quantity. It **excludes** postage, carriage, fees, manual
adjustments, discounts, samples, bad debt, gift vouchers and test codes (rule
R04). `unit_price` is stored as `DECIMAL(12,3)`, so sums are exact.

## Removal rules

| Rule | What it removes | Why |
|---|---|---|
| **R01 Sheet overlap** | Rows in the earlier workbook sheet dated on/after the later sheet's first timestamp (1–9 Dec 2010) | The two sheets overlap; the later sheet's copy is the one kept. A check (`dq_overlap_check`) proves the dropped copies match the kept ones row-for-row before removal counts. |
| **R02 Exact-looking repeat** | No removal. Later rows identical across all eight source fields are retained and flagged. | The source has no immutable line identifier; repeated scans/items cannot be distinguished from system duplicates. Both treatments are published as a sensitivity analysis. |
| **R03 Missing key field** | Blank invoice, stock code, timestamp, quantity or price | Cannot be attributed. |
| **R04 Non-product code** | POST, DOT, C2, C3, M, D, S, B, ADJUST, BANK CHARGES, AMAZONFEE, CRUK, TEST\*, GIFT / gift vouchers | Not product sales; outside the revenue definition. |
| **R05 Zero price** | `unit_price = 0` | Stock adjustments (damaged/missing/found) and free items — no revenue, would distort unit prices. |
| **R06 Negative price** | `unit_price < 0` | Accounting adjustments. |
| **R07 Non-positive qty on a sale** | Non-cancellation invoice with `quantity ≤ 0` | Stock movements, not sales. |
| **R08 Non-negative qty on a cancellation** | `C` invoice with `quantity ≥ 0` | Inconsistent records. |

## Flags (rows kept, but recorded)

| Flag | Meaning | Downstream handling |
|---|---|---|
| **F01 Missing customer** | ~22% of lines have no customer ID (`customer_key = -1`) | Included in revenue totals; excluded from segmentation, cohorts and CLV. |
| **F02 Extreme line** | `|quantity| ≥ 5000` or `|line value| ≥ £5000` (thresholds in `config/settings.toml`) | Kept; outlier-sensitive analyses may exclude them and must say so. |
| **F03 Exact-looking repeat** | A later line is identical across the eight supplied source fields after proven sheet overlap is removed. | Kept in production metrics; alternative exclusion totals appear in the data-quality report. |

## Duplicate policy

The two source sheets overlap for 1–9 December 2010. R01 removes 22,523 rows
from the earlier sheet only because a multiset comparison proves that all 22,523
have matching copies in the later sheet. That evidence does not exist for
same-sheet repeated lines. Some invoices contain many identical one-unit lines,
which can represent legitimate repeated items or scans. Because the source lacks
a transaction-line identifier, the pipeline retains these ambiguous rows, flags
them, and publishes an exclusion sensitivity rather than silently choosing one
interpretation.

Informational checks (`I01`–`I06` in the quality report) cover products with
several descriptions, stock-code case variants, multi-timestamp invoices,
partial months and left-censored / cancellation-only customers. These are not
removed — they are warnings for later milestones.
