"""M1 acceptance: star-schema keys are unique and not null, with valid relationships."""

from __future__ import annotations

import pytest

DIM_KEYS = {
    "dim_customer": "customer_key",
    "dim_product": "product_key",
    "dim_date": "date_key",
    "dim_country": "country_key",
}


@pytest.mark.parametrize("table,key", DIM_KEYS.items())
def test_dimension_key_unique_and_not_null(con, table, key):
    nulls = con.execute(f"select count(*) from {table} where {key} is null").fetchone()[0]
    assert nulls == 0, f"{table}.{key} has nulls"
    total, distinct = con.execute(
        f"select count(*), count(distinct {key}) from {table}"
    ).fetchone()
    assert total == distinct, f"{table}.{key} is not unique"


def test_fact_line_id_unique_and_not_null(con):
    total, distinct, nulls = con.execute(
        "select count(*), count(distinct line_id), count(*) filter (where line_id is null) "
        "from fct_order_lines"
    ).fetchone()
    assert nulls == 0
    assert total == distinct


@pytest.mark.parametrize(
    "fk,dim,dim_key",
    [
        ("customer_key", "dim_customer", "customer_key"),
        ("product_key", "dim_product", "product_key"),
        ("date_key", "dim_date", "date_key"),
        ("country_key", "dim_country", "country_key"),
    ],
)
def test_fact_foreign_keys_resolve(con, fk, dim, dim_key):
    orphans = con.execute(
        f"select count(*) from fct_order_lines f "
        f"left join {dim} d on f.{fk} = d.{dim_key} where d.{dim_key} is null"
    ).fetchone()[0]
    assert orphans == 0, f"fct_order_lines.{fk} has {orphans} values missing from {dim}"


def test_fact_keys_never_null(con):
    nulls = con.execute(
        "select count(*) from fct_order_lines where customer_key is null "
        "or product_key is null or date_key is null or country_key is null"
    ).fetchone()[0]
    assert nulls == 0
