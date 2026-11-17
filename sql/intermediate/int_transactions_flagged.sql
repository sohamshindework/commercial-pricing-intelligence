-- int_transactions_flagged: every staged row plus one boolean per cleaning rule
-- and the FIRST rule that removes it (exclusion_rule; NULL = row is kept).
-- Rule definitions and rationale: sql/seeds/cleaning_rules.csv and
-- docs/data_cleaning_rules.md. Rule order matters: each removed row is counted
-- against exactly one rule, so the data-quality report adds up.

create or replace table int_transactions_flagged as
with sheet_bounds as (
    -- First timestamp of each sheet and of the sheet that follows it.
    select
        source_sheet_number,
        lead(min(invoice_ts)) over (order by source_sheet_number) as next_sheet_start
    from stg_transactions
    group by source_sheet_number
),

with_overlap as (
    select
        t.*,
        coalesce(t.invoice_ts >= b.next_sheet_start, false) as r01_sheet_overlap
    from stg_transactions as t
    join sheet_bounds as b using (source_sheet_number)
),

with_duplicate_ambiguity as (
    select
        *,
        -- Exact-looking repeats are ranked only among rows that survive R01.
        -- The source has no immutable transaction-line identifier, so this is
        -- an uncertainty flag, not evidence that the later row is erroneous.
        row_number() over (
            partition by
                r01_sheet_overlap, invoice_no, stock_code_raw, description_raw, quantity,
                invoice_ts, price_raw, customer_id, country
            order by line_id
        ) > 1 as r02_exact_duplicate
    from with_overlap
),

with_rules as (
    select
        d.*,
        (d.invoice_no is null or d.stock_code is null or d.invoice_ts is null
            or d.quantity is null or d.unit_price is null)               as r03_missing_key_field,
        npc.category is not null                                         as r04_non_product_code,
        npc.category                                                     as non_product_category,
        coalesce(d.unit_price = 0, false)                                as r05_zero_price,
        coalesce(d.unit_price < 0, false)                                as r06_negative_price,
        coalesce(not d.is_cancellation_invoice and d.quantity <= 0, false)
                                                                         as r07_nonpositive_qty_on_sale,
        coalesce(d.is_cancellation_invoice and d.quantity >= 0, false)
                                                                         as r08_nonnegative_qty_on_cancellation
    from with_duplicate_ambiguity as d
    left join (
        -- One category per stock code (exact matches take priority over prefixes).
        select
            t.stock_code,
            arg_min(s.category, case s.match_type when 'exact' then 0 else 1 end) as category
        from (select distinct stock_code from stg_transactions) as t
        join seed_non_product_codes as s
            on (s.match_type = 'exact' and t.stock_code = s.stock_code)
            or (s.match_type = 'prefix' and starts_with(t.stock_code, s.stock_code))
        group by t.stock_code
    ) as npc using (stock_code)
)

select
    *,
    case
        when r01_sheet_overlap                   then 'R01_sheet_overlap'
        when r03_missing_key_field               then 'R03_missing_key_field'
        when r04_non_product_code                then 'R04_non_product_code'
        when r05_zero_price                      then 'R05_zero_price'
        when r06_negative_price                  then 'R06_negative_price'
        when r07_nonpositive_qty_on_sale         then 'R07_nonpositive_qty_on_sale'
        when r08_nonnegative_qty_on_cancellation then 'R08_nonnegative_qty_on_cancellation'
    end as exclusion_rule
from with_rules;
