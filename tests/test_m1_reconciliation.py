"""M1 acceptance: cleaned revenue reconciles to raw minus documented exclusions."""

from __future__ import annotations


def test_rows_reconcile_exactly(pipeline_result):
    r = pipeline_result
    assert r.raw_rows == r.removed_rows + r.kept_rows
    assert r.row_difference == 0


def test_value_reconciles_to_the_penny(pipeline_result):
    # Exact DECIMAL arithmetic: difference must be zero, not merely small.
    assert pipeline_result.value_difference == 0.0


def test_net_is_gross_plus_cancellations(pipeline_result):
    r = pipeline_result
    assert abs(r.net_revenue - (r.gross_revenue + r.cancellations)) <= 0.005


def test_sheet_overlap_fully_matched(pipeline_result):
    assert pipeline_result.overlap_unmatched == 0


def test_duplicate_sensitivity_keeps_invoice_counts_and_reconciles(con):
    rows = con.execute(
        "select * from dq_duplicate_sensitivity order by duplicate_policy"
    ).df().set_index("duplicate_policy")
    keep = rows.loc["retain_ambiguous"]
    exclude = rows.loc["exclude_repeat_lookalikes"]
    assert keep["fact_lines"] > exclude["fact_lines"]
    assert keep["net_revenue"] != exclude["net_revenue"]
    assert keep["sale_invoices"] == exclude["sale_invoices"]
    assert keep["cancellation_invoices"] == exclude["cancellation_invoices"]
    assert keep["net_revenue"] == keep["gross_revenue"] + keep["cancellations"]


def test_rule_rows_sum_to_removed(con, pipeline_result):
    total = con.execute("select coalesce(sum(rows_removed),0) from dq_rule_summary").fetchone()[0]
    assert total == pipeline_result.removed_rows


def test_value_removed_sums_to_raw_minus_net(con):
    raw_value, net = con.execute(
        "select (select raw_value from dq_reconciliation), "
        "(select net_revenue from dq_reconciliation)"
    ).fetchone()
    removed = con.execute("select sum(value_removed_gbp) from dq_rule_summary").fetchone()[0]
    assert abs(float(raw_value) - float(net) - float(removed)) <= 0.005
