-- fct_order_lines: grain = one kept invoice line (sale or cancellation).
-- Keys: line_id (unique), date_key -> dim_date, customer_key -> dim_customer
-- (-1 = unknown), product_key -> dim_product, country_key -> dim_country.
-- Money: unit_price and line_amount are exact DECIMALs in GBP.
-- Invoice semantics: sale invoices and cancellation invoices must be counted
-- separately from line_type. Gross sales AOV = sale line_amount / sale invoices;
-- cancellations remain in net revenue and are never included in the AOV denominator.
-- See int_order_lines.sql for the revenue definition.

create or replace table fct_order_lines as
select
    l.line_id,
    l.invoice_no,
    l.line_type,
    l.is_cancellation,
    l.invoice_ts,
    cast(strftime(l.invoice_date, '%Y%m%d') as integer) as date_key,
    l.invoice_date,
    coalesce(l.customer_id, -1)                         as customer_key,
    l.has_customer_id,
    l.stock_code                                        as product_key,
    c.country_key,
    l.quantity,
    l.unit_price,
    l.line_amount,
    l.is_duplicate_looking,
    l.is_extreme_line,
    l.source_sheet,
    l.source_row
from int_order_lines as l
left join dim_country as c on c.country_name = l.country
order by l.line_id;
