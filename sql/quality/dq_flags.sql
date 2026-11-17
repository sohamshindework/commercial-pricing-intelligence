-- dq_flags: issues that are kept in the data but must be known to every analysis.
-- One row per check: rows affected, value affected (GBP, net) and a share of net revenue.

create or replace table dq_flags as
with total as (
    select count(*) as n, sum(line_amount) as v from fct_order_lines
),
checks as (
    select 'F01_missing_customer' as check_id,
           'Kept lines without a customer ID' as description,
           count(*) as rows_affected, coalesce(sum(line_amount), 0) as value_gbp
    from fct_order_lines where not has_customer_id
    union all
    select 'F02_extreme_line',
           'Kept lines at or above the extreme quantity/value thresholds',
           count(*), coalesce(sum(line_amount), 0)
    from fct_order_lines where is_extreme_line
    union all
    select 'F03_duplicate_looking_line',
           'Exact-looking repeat lines retained because source line identity is unavailable',
           count(*), coalesce(sum(line_amount), 0)
    from fct_order_lines where is_duplicate_looking
    union all
    select 'I01_multi_description_products',
           'Products whose stock code carries more than one description (count of products)',
           count(*), null
    from dim_product where n_descriptions > 1
    union all
    select 'I02_code_case_variants',
           'Products whose stock code appears in more than one letter case (count of products)',
           count(*), null
    from dim_product where n_raw_code_variants > 1
    union all
    select 'I03_multi_timestamp_invoices',
           'Kept invoices with lines at more than one timestamp (count of invoices)',
           count(*), null
    from (
        select invoice_no from fct_order_lines group by invoice_no
        having count(distinct invoice_ts) > 1
    )
    union all
    select 'I04_partial_months',
           'Calendar months only partly covered by the data (count of months)',
           count(distinct month_start), null
    from dim_date where is_partial_month
    union all
    select 'I05_left_censored_customers',
           'Customers whose first purchase is in the first month of data (count of customers)',
           count(*), null
    from dim_customer where is_left_censored
    union all
    select 'I06_cancellation_only_customers',
           'Customers with cancellations but no kept sale line (count of customers)',
           count(*), null
    from dim_customer where has_only_cancellations
)
select
    c.*,
    case when c.value_gbp is null then null
         else round(100.0 * c.value_gbp / t.v, 2) end as pct_of_net_revenue
from checks as c, total as t;
