"""Shared fixtures: build the warehouse once from the committed sample Parquet."""

from __future__ import annotations

import duckdb
import pytest

from commercial_intelligence.common.config import repo_path
from commercial_intelligence.ingestion.pipeline import SEEDS, SQL_STEPS, load_seeds, run_pipeline

FIXTURE = repo_path("tests/fixtures/online_retail_ii_sample.parquet")


@pytest.fixture(scope="session")
def pipeline_result():
    assert FIXTURE.exists(), f"Missing fixture {FIXTURE}; run scripts/make_fixture.py"
    return run_pipeline(FIXTURE, check=False)


@pytest.fixture(scope="session")
def con():
    """An in-memory warehouse built from the fixture, shared read-only across tests."""
    import commercial_intelligence.ingestion.pipeline as pl

    c = duckdb.connect()
    c.execute(
        "create table raw_transactions as select * from read_parquet(?)", [str(FIXTURE)]
    )
    load_seeds(c)
    from commercial_intelligence.common.config import load_settings

    pl.set_config_variables(c, load_settings())
    for layer, name in SQL_STEPS:
        c.execute((pl.SQL_DIR / layer / f"{name}.sql").read_text())
    yield c
    c.close()


__all__ = ["SEEDS", "FIXTURE"]
