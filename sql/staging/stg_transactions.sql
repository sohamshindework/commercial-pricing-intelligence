-- stg_transactions: raw rows, typed and renamed. One row per source row.
-- No rows are removed here; only types and whitespace are normalised.
--
-- Input:  raw_transactions (landing Parquet, loaded by the runner)
-- Notes:
--   * line_id is a stable lineage key: sheet number * 1,000,000 + Excel row.
--   * unit_price is DECIMAL(12,3): every source price has at most 3 decimals
--     (checked by tests), so money sums are exact rather than floating point.
--   * stock_code is upper-cased: '85123a' and '85123A' are the same product.
--     The original code is kept as stock_code_raw.

create or replace table stg_transactions as
with sheets as (
    select
        source_sheet,
        row_number() over (order by min("InvoiceDate")) as sheet_number
    from raw_transactions
    group by source_sheet
)
select
    s.sheet_number * 1000000 + r.source_row                       as line_id,
    r.source_sheet,
    s.sheet_number                                                 as source_sheet_number,
    r.source_row,
    trim(r."Invoice")                                              as invoice_no,
    starts_with(trim(r."Invoice"), 'C')                            as is_cancellation_invoice,
    trim(r."StockCode")                                            as stock_code_raw,
    upper(trim(r."StockCode"))                                     as stock_code,
    nullif(trim(regexp_replace(r."Description", '\s+', ' ', 'g')), '') as description,
    r."Description"                                                as description_raw,
    cast(r."Quantity" as bigint)                                   as quantity,
    cast(r."InvoiceDate" as timestamp)                             as invoice_ts,
    cast(r."InvoiceDate" as date)                                  as invoice_date,
    r."Price"                                                      as price_raw,
    cast(round(r."Price", 3) as decimal(12, 3))                    as unit_price,
    cast(r."Quantity" as bigint) * cast(round(r."Price", 3) as decimal(12, 3)) as line_amount,
    cast(r."Customer ID" as bigint)                                as customer_id,
    trim(r."Country")                                              as country
from raw_transactions as r
join sheets as s using (source_sheet);
