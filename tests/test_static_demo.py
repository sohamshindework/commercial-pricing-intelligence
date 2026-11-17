"""B5 static portfolio export, reconciliation and privacy regression tests."""

from __future__ import annotations

import json
import runpy
from pathlib import Path

import pytest

SNAPSHOT = Path("web/public/data/portfolio-demo.json")
EXPORTER = runpy.run_path("scripts/export_static_demo.py")
EXPECTED = EXPORTER["EXPECTED"]
build_snapshot = EXPORTER["build_snapshot"]
validate_snapshot = EXPORTER["validate_snapshot"]


@pytest.fixture(scope="module")
def published() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def test_published_snapshot_matches_b4_regressions(published):
    validate_snapshot(published, require_full_dataset=False)
    kpis = published["filtered"]["market=*&family=*"]["overview"]["kpis"]
    experiment = published["fixed"]["experiment_summary"]
    classification = published["fixed"]["classification"]
    assert published["provenance"]["source_transactions"] == EXPECTED["source_transactions"]
    assert published["provenance"]["retained_transactions"] == EXPECTED["retained_transactions"]
    assert round(kpis["net_revenue"], 2) == EXPECTED["net_revenue"]
    assert kpis["sale_invoices"] == EXPECTED["sale_invoices"]
    assert kpis["cancellation_invoices"] == EXPECTED["cancellation_invoices"]
    assert round(kpis["gross_sales_aov"], 2) == EXPECTED["gross_sales_aov"]
    assert round(classification["metrics"][0]["macro_f1"], 3) == EXPECTED["classification_macro_f1"]
    assert experiment["available_products_per_arm"] == EXPECTED["available_products_per_arm"]
    assert experiment["required_products_per_arm"] == EXPECTED["required_products_per_arm"]
    assert experiment["adequately_powered"] is False


def test_every_filter_selection_reconciles_and_has_products(published):
    metadata = published["metadata"]
    expected_selections = (len(metadata["markets"]) + 1) * (len(metadata["families"]) + 1)
    assert len(published["filtered"]) == expected_selections
    for selection in published["filtered"].values():
        kpis = selection["overview"]["kpis"]
        assert kpis["net_revenue"] == pytest.approx(
            kpis["gross_revenue"] + kpis["cancellations"]
        )
        if kpis["sale_invoices"]:
            assert kpis["gross_sales_aov"] == pytest.approx(
                kpis["gross_revenue"] / kpis["sale_invoices"]
            )
        assert selection["products"]["total"] == len(selection["products"]["items"])


def test_snapshot_excludes_private_and_transaction_level_fields(published):
    raw = SNAPSHOT.read_text(encoding="utf-8")
    for forbidden in (
        '"customer_key"',
        '"customer_id"',
        '"invoice_no"',
        '"source_row"',
        "/Users/",
        ".duckdb",
    ):
        assert forbidden not in raw
    assert published["provenance"]["published_data"].startswith("Aggregate")


def test_export_is_deterministic_for_the_same_analytical_state():
    first = build_snapshot()
    second = build_snapshot()
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(
        second, sort_keys=True, separators=(",", ":")
    )


def test_static_host_configuration_preserves_spa_routes():
    config = json.loads(Path("web/vercel.json").read_text(encoding="utf-8"))
    assert config["buildCommand"] == "npm run build:demo"
    assert config["outputDirectory"] == "dist"
    assert {"source": "/(.*)", "destination": "/index.html"} in config["rewrites"]
