-- dim_customer: one row per customer ID, plus an "unknown" member (customer_key = -1)
-- for lines without a customer ID, so the fact table never has a null key.
--
-- * primary_country: country with the highest net revenue for that customer
--   (a few customers order from more than one country).
-- * first_purchase_date / cohort_month: based on the first SALE line, not cancellations.
-- * is_left_censored: the cohort is the first month of data. These customers may
--   have bought before the data starts, so their "first purchase" is not truly first.

create or replace table dim_customer as
with by_country as (
    select
        customer_id,
        country,
        sum(line_amount) as net_revenue,
        max(invoice_ts)  as last_ts
    from int_order_lines
    where customer_id is not null
    group by customer_id, country
),

primary_country as (
    select
        customer_id,
        arg_max(country, (net_revenue, last_ts)) as primary_country,
        count(*)                                 as n_countries
    from by_country
    group by customer_id
),

activity as (
    select
        customer_id,
        min(invoice_date) filter (where line_type = 'sale') as first_purchase_date,
        max(invoice_date) filter (where line_type = 'sale') as last_purchase_date
    from int_order_lines
    where customer_id is not null
    group by customer_id
),

data_start as (
    select date_trunc('month', min(invoice_date)) as first_month from int_order_lines
)

select
    a.customer_id                                          as customer_key,
    a.customer_id,
    p.primary_country,
    p.n_countries,
    a.first_purchase_date,
    a.last_purchase_date,
    cast(date_trunc('month', a.first_purchase_date) as date) as cohort_month,
    coalesce(date_trunc('month', a.first_purchase_date) = ds.first_month, false)
                                                           as is_left_censored,
    a.first_purchase_date is null                          as has_only_cancellations,
    false                                                  as is_unknown
from activity as a
join primary_country as p using (customer_id)
cross join data_start as ds

union all

select
    -1, null, null, null, null, null, null, false, false, true;
