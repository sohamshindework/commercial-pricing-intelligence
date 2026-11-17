-- dq_reconciliation: raw total = removed total + kept total, exactly.
-- Values are DECIMAL(38,3) sums of quantity * unit_price, so the identity holds
-- to a tenth of a penny with no floating-point tolerance.
-- row_difference and value_difference must both be 0 (the runner checks this).

create or replace table dq_reconciliation as
with raw as (
    select count(*) as raw_rows, sum(line_amount) as raw_value from stg_transactions
),
removed as (
    select sum(rows_removed) as removed_rows, sum(value_removed_gbp) as removed_value
    from dq_rule_summary
),
kept as (
    select
        count(*)                                              as kept_rows,
        sum(line_amount)                                      as net_revenue,
        sum(line_amount) filter (where line_type = 'sale')         as gross_revenue,
        coalesce(sum(line_amount) filter (where line_type = 'cancellation'), 0) as cancellations
    from fct_order_lines
)
select
    raw.raw_rows,
    raw.raw_value,
    removed.removed_rows,
    removed.removed_value,
    kept.kept_rows,
    kept.gross_revenue,
    kept.cancellations,
    kept.net_revenue,
    raw.raw_rows - removed.removed_rows - kept.kept_rows        as row_difference,
    raw.raw_value - removed.removed_value - kept.net_revenue    as value_difference
from raw, removed, kept;
