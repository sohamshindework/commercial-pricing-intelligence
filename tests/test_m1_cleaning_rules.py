"""M1: each cleaning rule removes what it claims, and nothing it should keep."""

from __future__ import annotations


def test_no_kept_line_breaks_any_removal_rule(con):
    # Every surviving line must be a product line with positive price and a
    # quantity whose sign agrees with the invoice type.
    bad = con.execute(
        """
        select count(*) from fct_order_lines
        where unit_price <= 0
           or (line_type = 'sale' and quantity <= 0)
           or (line_type = 'cancellation' and quantity >= 0)
        """
    ).fetchone()[0]
    assert bad == 0


def test_non_product_codes_removed(con):
    kept = con.execute(
        "select count(*) from fct_order_lines where product_key in "
        "('POST','DOT','M','D','S','B','C2','C3','BANK CHARGES','AMAZONFEE','ADJUST','GIFT')"
    ).fetchone()[0]
    assert kept == 0


def test_each_removed_row_has_exactly_one_rule(con):
    # exclusion_rule is the first matched rule; it must be set iff the row is removed.
    mismatched = con.execute(
        """
        select count(*) from int_transactions_flagged
        where (exclusion_rule is null) <> (
            not (r01_sheet_overlap or r03_missing_key_field
                 or r04_non_product_code or r05_zero_price or r06_negative_price
                 or r07_nonpositive_qty_on_sale or r08_nonnegative_qty_on_cancellation))
        """
    ).fetchone()[0]
    assert mismatched == 0


def test_exact_looking_repeats_are_flagged_not_silently_removed(con):
    ambiguous = con.execute(
        "select count(*) from fct_order_lines where is_duplicate_looking"
    ).fetchone()[0]
    assert ambiguous > 0
    wrongly_removed = con.execute(
        "select count(*) from int_transactions_flagged "
        "where exclusion_rule = 'R02_exact_duplicate'"
    ).fetchone()[0]
    assert wrongly_removed == 0


def test_kept_lines_have_no_exclusion_rule(con):
    kept = con.execute("select count(*) from int_order_lines").fetchone()[0]
    clean = con.execute(
        "select count(*) from int_transactions_flagged where exclusion_rule is null"
    ).fetchone()[0]
    assert kept == clean


def test_unknown_customer_member_exists_and_is_minus_one(con):
    row = con.execute(
        "select customer_key from dim_customer where is_unknown"
    ).fetchall()
    assert row == [(-1,)]


def test_missing_customer_lines_map_to_unknown(con):
    mismatched = con.execute(
        "select count(*) from fct_order_lines "
        "where has_customer_id = (customer_key = -1)"
    ).fetchone()[0]
    assert mismatched == 0
