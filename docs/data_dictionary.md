# Data dictionary — star schema

Exported to `data/exports/powerbi/` (Parquet + CSV) by `scripts/export_powerbi.py`.
Grain and keys below; see [`data_cleaning_rules.md`](data_cleaning_rules.md) for
the revenue definition.

## fct_order_lines (fact) — one row per kept invoice line

| Column | Type | Notes |
|---|---|---|
| line_id | int64 | unique line key |
| invoice_no | string | invoice; `C…` = cancellation |
| line_type | string | `sale` or `cancellation` |
| invoice_ts / invoice_date | timestamp / date | booking time |
| date_key | int64 | → dim_date |
| customer_key | int64 | → dim_customer; **-1 = guest/unknown** |
| product_key | string | → dim_product (upper-cased stock code) |
| country_key | int64 | → dim_country |
| quantity | int64 | >0 sale, <0 cancellation |
| unit_price | decimal(12,3) | GBP |
| line_amount | decimal | `quantity × unit_price`, GBP |
| is_duplicate_looking | boolean | exact-looking repeat retained under the documented uncertainty policy (F03) |
| is_extreme_line | boolean | very large qty/value (F02 flag) |

### Invoice measures

- **Sale invoices:** distinct `invoice_no` on `line_type='sale'`.
- **Cancellation invoices:** distinct `invoice_no` on `line_type='cancellation'`.
- **Net revenue:** all `line_amount`, so cancellations retain their negative impact.
- **Gross sales AOV:** gross sale-line revenue divided by sale invoices. Cancellation
  invoices are reported separately and are not included in its denominator.

## dim_date — contiguous calendar (marked date table)

| Column | Type | Notes |
|---|---|---|
| date_key | int64 | `yyyymmdd` |
| date | date | |
| year, quarter, month | int64 | |
| month_name | string | sorted by month |
| year_month | string | `YYYY-MM` |
| is_partial_month | boolean | month only partly covered by data |

## dim_customer — one row per customer (+ `-1` unknown)

| Column | Type | Notes |
|---|---|---|
| customer_key | int64 | `-1` = guest/unknown member |
| primary_country | string | highest-revenue country |
| first_purchase_date, cohort_month | date | first sale |
| is_left_censored | boolean | acquired in first data month |
| is_unknown | boolean | the guest member |

## dim_product — one row per stock code (+ family from M4)

| Column | Type | Notes |
|---|---|---|
| product_key / stock_code | string | upper-cased code |
| product_name | string | most frequent description |
| family_code / family | string | M4 classification (`NA`/Unclassified if none) |
| first_sale_date, last_sale_date | date | |

## dim_country — one row per country

| Column | Type | Notes |
|---|---|---|
| country_key | int64 | |
| country_name | string | |
| region | string | EU / Other Europe / Rest of World / UK |
| market | string | UK / International / Unknown |

## Imported analytics tables (pre-computed in Python)

| Table | Source | Grain |
|---|---|---|
| revenue_bridges | `exports/revenue/bridges.parquet` | lens × comparison × component |
| monthly_revenue | `exports/revenue/monthly.parquet` | year_month |
| clv_customers | `exports/customers/clv_customers.parquet` | customer |
| cohort_retention_curve | `exports/customers/retention_curve.parquet` | month_offset |
| opportunities | `exports/pricing/opportunities.parquet` | opportunity |
