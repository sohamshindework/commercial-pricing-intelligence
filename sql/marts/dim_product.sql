-- dim_product: one row per (upper-cased) stock code that has at least one kept line.
-- The same stock code can carry several descriptions (typos, renames, notes).
-- product_name is the most frequent description on kept lines; ties go to the
-- most recently used one, then alphabetical order, so the choice is deterministic.

create or replace table dim_product as
with description_counts as (
    select
        stock_code,
        description,
        count(*)        as n_lines,
        max(invoice_ts) as last_used
    from int_order_lines
    where description is not null
    group by stock_code, description
),

ranked as (
    select
        *,
        row_number() over (
            partition by stock_code
            order by n_lines desc, last_used desc, description
        ) as rn
    from description_counts
),

activity as (
    select
        stock_code,
        min(invoice_date) filter (where line_type = 'sale') as first_sale_date,
        max(invoice_date) filter (where line_type = 'sale') as last_sale_date,
        count(distinct stock_code_raw)                     as n_raw_code_variants
    from int_order_lines
    group by stock_code
)

select
    a.stock_code                                         as product_key,
    a.stock_code,
    coalesce(r.description, 'UNKNOWN (' || a.stock_code || ')') as product_name,
    coalesce(dc.n_descriptions, 0)                       as n_descriptions,
    a.n_raw_code_variants,
    starts_with(a.stock_code, 'DCGS')                    as is_dotcom_code,
    a.first_sale_date,
    a.last_sale_date
from activity as a
left join ranked as r on r.stock_code = a.stock_code and r.rn = 1
left join (
    select stock_code, count(*) as n_descriptions from description_counts group by stock_code
) as dc on dc.stock_code = a.stock_code;
