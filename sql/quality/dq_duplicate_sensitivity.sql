-- dq_duplicate_sensitivity: core measures under both plausible treatments of
-- exact-looking repeated lines. The production policy retains them because the
-- source has no immutable line identifier. The exclusion scenario is published
-- as sensitivity only; proven cross-sheet overlap remains removed in both.

create or replace table dq_duplicate_sensitivity as
with scenarios as (
    select 'retain_ambiguous' as duplicate_policy, true as include_ambiguous
    union all
    select 'exclude_repeat_lookalikes', false
),
metrics as (
    select
        s.duplicate_policy,
        count(*) as fact_lines,
        sum(f.quantity) filter (where f.line_type = 'sale') as sale_units,
        coalesce(sum(f.quantity) filter (where f.line_type = 'cancellation'), 0)
            as cancellation_units,
        sum(f.line_amount) filter (where f.line_type = 'sale') as gross_revenue,
        coalesce(sum(f.line_amount) filter (where f.line_type = 'cancellation'), 0)
            as cancellations,
        sum(f.line_amount) as net_revenue,
        count(distinct f.invoice_no) filter (where f.line_type = 'sale') as sale_invoices,
        count(distinct f.invoice_no) filter (where f.line_type = 'cancellation')
            as cancellation_invoices,
        count(distinct f.invoice_no) as all_invoices
    from scenarios as s
    join fct_order_lines as f
      on s.include_ambiguous or not f.is_duplicate_looking
    group by s.duplicate_policy
)
select
    *,
    gross_revenue / nullif(sale_invoices, 0) as gross_sales_aov
from metrics
order by case duplicate_policy when 'retain_ambiguous' then 1 else 2 end;
