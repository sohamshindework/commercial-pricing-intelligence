-- dq_overlap_check: proves rule R01 only drops true copies.
-- For each pair of consecutive sheets, compare the rows dropped from the earlier
-- sheet with the rows of the later sheet in the same time window, as multisets of
-- all eight source fields. unmatched_rows must be 0 (the runner checks this).

create or replace table dq_overlap_check as
with windows as (
    select
        f.source_sheet_number                 as earlier_sheet,
        f.source_sheet_number + 1             as later_sheet,
        min(f.invoice_ts)                     as window_start,
        max(f.invoice_ts)                     as window_end
    from int_transactions_flagged as f
    where f.r01_sheet_overlap
    group by f.source_sheet_number
),

earlier as (
    select w.earlier_sheet, invoice_no, stock_code_raw, description_raw, quantity, invoice_ts,
           price_raw, customer_id, country, count(*) as n
    from int_transactions_flagged as f
    join windows as w on f.source_sheet_number = w.earlier_sheet
    where f.r01_sheet_overlap
    group by all
),

later as (
    select w.earlier_sheet, invoice_no, stock_code_raw, description_raw, quantity, invoice_ts,
           price_raw, customer_id, country, count(*) as n
    from int_transactions_flagged as f
    join windows as w
        on f.source_sheet_number = w.later_sheet
       and f.invoice_ts between w.window_start and w.window_end
    group by all
),

compared as (
    select
        coalesce(e.n, 0) as n_earlier,
        coalesce(l.n, 0) as n_later
    from earlier as e
    full outer join later as l
        on  e.earlier_sheet = l.earlier_sheet
        and e.invoice_no is not distinct from l.invoice_no
        and e.stock_code_raw is not distinct from l.stock_code_raw
        and e.description_raw is not distinct from l.description_raw
        and e.quantity is not distinct from l.quantity
        and e.invoice_ts is not distinct from l.invoice_ts
        and e.price_raw is not distinct from l.price_raw
        and e.customer_id is not distinct from l.customer_id
        and e.country is not distinct from l.country
)

select
    coalesce(sum(n_earlier), 0)                         as overlap_rows_dropped,
    coalesce(sum(n_later), 0)                           as matching_window_rows_kept,
    coalesce(sum(abs(n_earlier - n_later)), 0)          as unmatched_rows
from compared;
