-- int_order_lines: rows that pass every cleaning rule.
--
-- Revenue definition (used everywhere downstream):
--   * line_type = 'sale'         : product line on a normal invoice (quantity > 0, price > 0)
--   * line_type = 'cancellation' : product line on a 'C' credit note (quantity < 0, price > 0)
--   * gross product revenue  = sum(line_amount) over sale lines
--   * cancellations          = sum(line_amount) over cancellation lines (negative)
--   * net product revenue    = gross + cancellations, booked on the invoice date
--   All amounts are GBP, excluding postage, fees and adjustments (rule R04).
--
-- Flags (rows are kept):
--   * has_customer_id = false  -> guest / unidentified buyer (F01)
--   * is_extreme_line = true   -> very large quantity or value (F02)
--   * is_duplicate_looking = true -> exact-looking repeat with unresolved
--     provenance; retained because the source has no line identifier (F03)

create or replace table int_order_lines as
select
    line_id,
    source_sheet,
    source_row,
    invoice_no,
    case when is_cancellation_invoice then 'cancellation' else 'sale' end as line_type,
    is_cancellation_invoice                                               as is_cancellation,
    invoice_ts,
    invoice_date,
    stock_code,
    stock_code_raw,
    description,
    quantity,
    unit_price,
    line_amount,
    customer_id,
    customer_id is not null                                               as has_customer_id,
    country,
    r02_exact_duplicate                                                  as is_duplicate_looking,
    (abs(quantity) >= getvariable('extreme_quantity')
        or abs(line_amount) >= getvariable('extreme_line_value_gbp'))     as is_extreme_line
from int_transactions_flagged
where exclusion_rule is null;
