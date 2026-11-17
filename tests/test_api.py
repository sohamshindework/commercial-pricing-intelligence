"""Backend API integration and security tests.

FastAPI is a required dependency for this module. CI builds an ignored warehouse
and analytical exports from the committed sample before collecting these tests, so
a missing dependency or artifact is a hard failure rather than a silent skip.
"""

from __future__ import annotations

import duckdb
import pytest
from fastapi.testclient import TestClient

from commercial_intelligence.common.config import load_settings, repo_path
from commercial_intelligence.reporting import exports, queries

WAREHOUSE = repo_path(load_settings()["paths"]["warehouse"])


@pytest.fixture(scope="module")
def client():
    from api.main import app

    assert WAREHOUSE.exists(), "API tests require a built warehouse; run the documented pipeline."
    return TestClient(app)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_metadata(client):
    r = client.get("/api/metadata")
    assert r.status_code == 200
    body = r.json()
    assert body["currency"] == "GBP"
    assert set(body["markets"]) >= {"UK", "International"}
    assert len(body["families"]) >= 1
    assert "/api/revenue/bridge" in body["fixed_period_endpoints"]


def test_overview_reconciles_to_marts(client):
    body = client.get("/api/overview").json()["kpis"]
    # The endpoint must reconcile independently to whichever validated warehouse
    # is under test (full local data or the committed CI sample).
    con = duckdb.connect(str(WAREHOUSE), read_only=True)
    try:
        expected = con.execute(
            """
            select sum(line_amount),
                   count(distinct invoice_no) filter (where line_type='sale'),
                   count(distinct invoice_no) filter (where line_type='cancellation'),
                   count(distinct invoice_no)
            from fct_order_lines
            """
        ).fetchone()
    finally:
        con.close()
    assert body["net_revenue"] == pytest.approx(float(expected[0]))
    assert body["sale_invoices"] == expected[1]
    assert body["cancellation_invoices"] == expected[2]
    assert body["all_invoices"] == expected[3]
    assert body["gross_sales_aov"] == pytest.approx(
        body["gross_revenue"] / body["sale_invoices"]
    )
    assert body["net_revenue"] == pytest.approx(
        body["gross_revenue"] + body["cancellations"]
    )


def test_market_filter_reduces_revenue(client):
    all_rev = client.get("/api/overview").json()["kpis"]["net_revenue"]
    uk_rev = client.get("/api/overview", params={"market": "UK"}).json()["kpis"]["net_revenue"]
    assert 0 < uk_rev < all_rev


def test_invalid_market_rejected(client):
    r = client.get("/api/overview", params={"market": "Mars"})
    assert r.status_code == 422


def test_bad_date_range_rejected(client):
    r = client.get("/api/overview", params={"start": "2011-06-01", "end": "2011-01-01"})
    assert r.status_code == 422


def test_trend_is_ordered_and_filterable(client):
    pts = client.get("/api/revenue/trend", params={"market": "UK"}).json()["points"]
    months = [p["year_month"] for p in pts]
    assert months == sorted(months)
    assert len(pts) > 0


def test_bridge_is_fixed_period(client):
    body = client.get("/api/revenue/bridge", params={"lens": "product"}).json()
    assert body["interactive"] is False
    assert body["comparison_label"]
    kinds = {c["kind"] for c in body["components"]}
    assert {"start", "end"} <= kinds


def test_products_pagination(client):
    p1 = client.get("/api/products/top", params={"limit": 5, "offset": 0}).json()
    p2 = client.get("/api/products/top", params={"limit": 5, "offset": 5}).json()
    assert p1["total"] > 10
    assert len(p1["items"]) == 5
    assert p1["items"][0]["product_key"] != p2["items"][0]["product_key"]


def test_products_limit_validation(client):
    assert client.get("/api/products/top", params={"limit": 0}).status_code == 422
    assert client.get("/api/products/top", params={"limit": 999}).status_code == 422


def test_metadata_families_have_names(client):
    fams = client.get("/api/metadata").json()["families"]
    assert all(f.get("name") for f in fams)


def test_revenue_by_market_sums_to_overview(client):
    total = client.get("/api/overview").json()["kpis"]["net_revenue"]
    by_market = client.get("/api/revenue/by-market").json()["items"]
    assert abs(sum(m["net_revenue"] for m in by_market) - total) < 0.01
    assert {m["market"] for m in by_market} <= {"UK", "International", "Unknown"}


def test_by_family_respects_family_filter(client):
    one = client.get("/api/revenue/by-family", params={"family": "KD"}).json()["items"]
    # Filtering to one family returns only that family.
    assert [r["family_code"] for r in one] == ["KD"]


def test_customer_segments(client):
    items = client.get("/api/customers/segments").json()["items"]
    assert len(items) >= 3
    assert all(i["customers"] > 0 for i in items)


def test_customer_cohorts_offset_zero_full(client):
    body = client.get("/api/customers/cohorts").json()
    assert body["interactive"] is False
    assert 0 in body["offsets"]
    # Every cohort starts at 100% retention at offset 0.
    for c in body["cohorts"]:
        p0 = next((p for p in c["points"] if p["offset"] == 0), None)
        assert p0 and abs(p0["rate"] - 1.0) < 1e-6
    assert len(body["curve"]) > 0


def test_customer_clv(client):
    body = client.get("/api/customers/clv").json()
    assert body["winner"]
    assert any(m["method"] == "BG/NBD + Gamma-Gamma" for m in body["metrics"])
    assert sum(b["count"] for b in body["distribution"]) > 0
    assert body["avg_clv"] >= 0
    assert all(b["lower"] >= 0 for b in body["distribution"])


def test_pricing_opportunities_scale_with_capture(client):
    half = client.get(
        "/api/pricing/opportunities", params={"capture_low": 0.2, "capture_high": 0.5}
    ).json()["items"][0]
    # impact = measured gap x capture rate.
    assert abs(half["impact_low_gbp"] - half["measured_gap_gbp"] * 0.2) < 1.0
    assert abs(half["impact_high_gbp"] - half["measured_gap_gbp"] * 0.5) < 1.0
    # margin scenario is below the revenue range (no cost data => labelled scenario).
    assert half["margin_low_gbp"] < half["impact_low_gbp"]


def test_pricing_capture_validation(client):
    r = client.get(
        "/api/pricing/opportunities", params={"capture_low": 0.6, "capture_high": 0.3}
    )
    assert r.status_code == 422


def test_price_response_is_non_causal_note(client):
    body = client.get("/api/pricing/price-response").json()
    assert "not a price elasticity" in body["note"].lower()
    assert len(body["items"]) >= 1


def test_power_curve_monotonic(client):
    pts = client.get("/api/experiments/power-curve").json()["points"]
    mdes = [p["mde_relative"] for p in pts]
    # More sample => smaller detectable effect.
    assert mdes == sorted(mdes, reverse=True)


def test_experiment_summary_is_sku_level_and_honest(client):
    body = client.get("/api/experiments/summary").json()
    assert body["randomisation_unit"] == "SKU"
    assert body["analysis_unit"].startswith("SKU")
    assert body["required_products_per_arm"] > body["available_products_per_arm"]
    assert body["adequately_powered"] is False
    assert body["mde_available_relative"] > body["target_mde_relative"]


def test_executive_summary(client):
    body = client.get("/api/executive/summary").json()
    assert body["headline"]["net_revenue"] > 0
    assert len(body["recommendations"]) >= 3
    r = body["recommendations"][0]
    assert {"priority", "action", "evidence", "scenario_impact", "confidence"} <= set(r)
    assert len(body["monitoring_kpis"]) >= 3
    assert any("cost" in lim.lower() for lim in body["limitations"])


def test_classification_is_fixed_period(client):
    body = client.get("/api/products/classification").json()
    assert body["interactive"] is False
    assert body["chosen_method"]
    assert [m["method"] for m in body["metrics"]] == ["Baseline (TF-IDF + LogReg)"]
    assert "withdrawn" in body["period_note"].lower()
    assert len(body["per_class"]) >= 1
    assert all(0 <= row["f1"] <= 1 for row in body["per_class"])


def test_unknown_family_and_extreme_offset_are_rejected(client):
    assert client.get("/api/overview", params={"family": "../../etc/passwd"}).status_code == 422
    assert client.get("/api/overview", params={"family": "ZZ"}).status_code == 422
    assert client.get("/api/products/top", params={"offset": 100_001}).status_code == 422


def test_api_is_read_only_and_disables_external_access():
    con = queries.connect()
    try:
        with pytest.raises(duckdb.Error):
            con.execute("create table security_probe(value integer)")
        with pytest.raises(duckdb.Error):
            con.execute("select * from read_csv_auto('/tmp/not-allowed.csv')")
    finally:
        con.close()


def test_missing_export_error_does_not_expose_absolute_path(client, monkeypatch, tmp_path):
    monkeypatch.setattr(exports, "_exports_root", lambda: tmp_path / "private" / "exports")
    response = client.get("/api/customers/segments")
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert str(tmp_path) not in detail
    assert "Required analytical export" in detail


def test_unexpected_query_error_is_generic(monkeypatch, tmp_path):
    from api.main import app

    def fail_query(*_args, **_kwargs):
        raise duckdb.IOException(f"sensitive path {tmp_path / 'warehouse.duckdb'}")

    monkeypatch.setattr(queries, "overview_kpis", fail_query)
    response = TestClient(app, raise_server_exceptions=False).get("/api/overview")
    assert response.status_code == 503
    assert response.json() == {"detail": "The analytical query could not be completed."}
    assert str(tmp_path) not in response.text


def test_concurrency_limit_returns_retryable_error(client, monkeypatch):
    import api.deps as deps

    class NoCapacity:
        def acquire(self, *, blocking):
            assert blocking is False
            return False

        def release(self):  # pragma: no cover - should never be reached
            raise AssertionError("An unacquired slot must not be released")

    monkeypatch.setattr(deps, "_CONNECTION_SLOTS", NoCapacity())
    response = client.get("/api/overview")
    assert response.status_code == 503
    assert "busy" in response.json()["detail"].lower()


def test_query_watchdog_starts_and_resources_close(monkeypatch):
    import api.deps as deps

    events = []

    class FakeConnection:
        def interrupt(self):
            events.append("interrupt")

        def close(self):
            events.append("connection_close")

    class FakeTimer:
        daemon = False

        def __init__(self, seconds, callback):
            events.append(("timer_created", seconds))
            self.callback = callback

        def start(self):
            events.append("timer_start")

        def cancel(self):
            events.append("timer_cancel")

    connection = FakeConnection()
    monkeypatch.setattr(deps.queries, "connect", lambda **_kwargs: connection)
    monkeypatch.setattr(deps, "Timer", FakeTimer)

    dependency = deps.get_con()
    assert next(dependency) is connection
    dependency.close()
    assert events == [
        ("timer_created", deps.QUERY_TIMEOUT_SECONDS),
        "timer_start",
        "timer_cancel",
        "connection_close",
    ]


def test_host_cors_and_method_policy(client):
    assert client.get("/api/health", headers={"Host": "attacker.example"}).status_code == 400
    local = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert local.headers["access-control-allow-origin"] == "http://localhost:5173"
    remote = client.get("/api/health", headers={"Origin": "https://attacker.example"})
    assert "access-control-allow-origin" not in remote.headers
    assert client.post("/api/overview").status_code == 405
