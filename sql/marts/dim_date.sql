-- dim_date: contiguous calendar covering whole years around the data (a Power BI
-- date table must have no gaps). Flags tell analyses which days and months hold data.
--
-- * is_in_data_range: between the first and last transaction date.
-- * is_partial_month: the month is only partly covered by the data (e.g. the
--   data ends on 9 Dec 2011). Month-on-month and year-on-year comparisons must
--   exclude or pro-rate partial months.

create or replace table dim_date as
with bounds as (
    select min(invoice_date) as first_date, max(invoice_date) as last_date
    from int_order_lines
),

calendar as (
    select cast(d as date) as date
    from bounds,
        generate_series(
            cast(date_trunc('year', first_date) as date),
            cast(date_trunc('year', last_date) + interval 1 year - interval 1 day as date),
            interval 1 day
        ) as g(d)
),

trading_days as (
    select distinct invoice_date from int_order_lines
)

select
    cast(strftime(c.date, '%Y%m%d') as integer)            as date_key,
    c.date,
    year(c.date)                                           as year,
    quarter(c.date)                                        as quarter,
    month(c.date)                                          as month,
    strftime(c.date, '%B')                                 as month_name,
    strftime(c.date, '%Y-%m')                              as year_month,
    cast(date_trunc('month', c.date) as date)              as month_start,
    isoyear(c.date)                                        as iso_year,
    weekofyear(c.date)                                     as iso_week,
    isodow(c.date)                                         as iso_day_of_week,
    strftime(c.date, '%A')                                 as day_name,
    isodow(c.date) >= 6                                    as is_weekend,
    td.invoice_date is not null                            as has_transactions,
    c.date between b.first_date and b.last_date            as is_in_data_range,
    -- partial = month overlaps the data range but is not fully inside it
    (date_trunc('month', c.date) <= b.last_date
        and last_day(c.date) >= b.first_date
        and (date_trunc('month', c.date) < b.first_date or last_day(c.date) > b.last_date))
                                                           as is_partial_month
from calendar as c
cross join bounds as b
left join trading_days as td on td.invoice_date = c.date
order by c.date;
