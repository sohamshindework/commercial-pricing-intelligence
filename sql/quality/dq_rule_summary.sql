-- dq_rule_summary: rows, units and value removed by each cleaning rule.
-- Every removed row belongs to exactly one rule (the first that matched), so the
-- rows here add up to raw rows minus kept rows.

create or replace table dq_rule_summary as
select
    r.rule_id,
    r.rule_order,
    r.name,
    count(f.line_id)                                as rows_removed,
    coalesce(sum(f.quantity), 0)                    as units_removed,
    coalesce(sum(f.line_amount), 0)                 as value_removed_gbp
from seed_cleaning_rules as r
left join int_transactions_flagged as f on f.exclusion_rule = r.rule_id
where r.action = 'remove'
group by r.rule_id, r.rule_order, r.name
order by r.rule_order;
