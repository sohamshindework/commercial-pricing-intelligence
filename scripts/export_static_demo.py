"""Build the aggregate-only, deterministic data snapshot for the portfolio demo.

The exporter deliberately exercises the same FastAPI contracts as the local app.
It publishes no transaction rows or customer identifiers. Arbitrary date filtering
is excluded because supporting it faithfully would require a much finer-grained
public dataset than the portfolio demo needs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from commercial_intelligence.reporting import queries

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EXPECTED = {
    "source_transactions": 1_067_371,
    "retained_transactions": 1_033_062,
    "net_revenue": 18_981_261.52,
    "sale_invoices": 39_516,
    "cancellation_invoices": 7_406,
    "gross_sales_aov": 498.56,
    "classification_macro_f1": 0.873,
    "available_products_per_arm": 1_713,
    "required_products_per_arm": 21_102,
}


def _get(client: TestClient, path: str, params: dict[str, Any] | None = None) -> dict:
    response = client.get(path, params=params)
    response.raise_for_status()
    return response.json()


def _selection_key(market: str | None, family: str | None) -> str:
    return f"market={market or '*'}&family={family or '*'}"


def _all_products(client: TestClient, params: dict[str, str]) -> dict:
    items: list[dict] = []
    offset = 0
    total = None
    while total is None or offset < total:
        page = _get(
            client,
            "/api/products/top",
            {**params, "limit": 200, "offset": offset},
        )
        total = int(page["total"])
        items.extend(page["items"])
        offset += 200
    return {"filters": page["filters"], "items": items, "total": total}


def build_snapshot() -> dict:
    """Return the complete static snapshot using the validated API contracts."""
    from api.main import app

    with TestClient(app) as client:
        metadata = _get(client, "/api/metadata")
        filtered: dict[str, dict] = {}
        markets: list[str | None] = [None, *metadata["markets"]]
        families: list[str | None] = [
            None,
            *[family["family_code"] for family in metadata["families"]],
        ]
        for market in markets:
            for family in families:
                params = {
                    key: value
                    for key, value in {"market": market, "family": family}.items()
                    if value is not None
                }
                filtered[_selection_key(market, family)] = {
                    "overview": _get(client, "/api/overview", params),
                    "revenue_trend": _get(client, "/api/revenue/trend", params),
                    "revenue_by_family": _get(client, "/api/revenue/by-family", params),
                    "revenue_by_market": _get(client, "/api/revenue/by-market", params),
                    "products": _all_products(client, params),
                }

        fixed = {
            "bridge_product": _get(client, "/api/revenue/bridge", {"lens": "product"}),
            "bridge_customer": _get(client, "/api/revenue/bridge", {"lens": "customer"}),
            "bridge_geography": _get(client, "/api/revenue/bridge", {"lens": "geography"}),
            "classification": _get(client, "/api/products/classification"),
            "segments": _get(client, "/api/customers/segments"),
            "cohorts": _get(client, "/api/customers/cohorts"),
            "clv": _get(client, "/api/customers/clv"),
            "dispersion": _get(client, "/api/pricing/dispersion", {"limit": 15}),
            "price_response": _get(client, "/api/pricing/price-response"),
            "experiment_summary": _get(client, "/api/experiments/summary"),
            "power_curve": _get(client, "/api/experiments/power-curve"),
            "executive": _get(client, "/api/executive/summary"),
        }
        opportunities = {}
        grid = [round(step * 0.05, 2) for step in range(21)]
        for low in grid:
            for high in grid:
                if low <= high:
                    opportunities[f"{low:.2f}:{high:.2f}"] = _get(
                        client,
                        "/api/pricing/opportunities",
                        {"capture_low": low, "capture_high": high},
                    )

    core = {
        "metadata": metadata,
        "filtered": filtered,
        "fixed": fixed,
        "opportunities": opportunities,
    }
    fingerprint = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "schema_version": 1,
        "analytical_fingerprint_sha256": fingerprint,
        "provenance": {
            "dataset": "UCI Online Retail II",
            "dataset_license": "CC BY 4.0",
            "source_period": "2009-12-01 to 2011-12-09",
            "source_transactions": 1_067_371,
            "retained_transactions": 1_033_062,
            "scope": "Independent portfolio analysis using historical single-retailer data.",
            "published_data": "Aggregate API-equivalent responses only.",
            "excluded_data": [
                "transaction rows",
                "customer records and identifiers",
                "invoice identifiers",
                "raw archives and spreadsheets",
                "DuckDB warehouse files",
            ],
            "interaction_limitations": {
                "date_filters": (
                    "Disabled in static demo mode to avoid publishing fine-grained data. "
                    "Market and product-family filters remain exact."
                ),
                "models": "Fixed-period model outputs do not respond to global filters.",
                "pricing": (
                    "Capture sliders select precomputed scenarios; they are not causal forecasts."
                ),
            },
            "metric_definitions": {
                "net_revenue": "Gross product sales plus cancellation/credit-note value.",
                "sale_invoices": "Distinct invoices containing sale lines.",
                "cancellation_invoices": "Distinct invoices containing cancellation lines.",
                "gross_sales_aov": "Gross product sales divided by distinct sale invoices.",
                "customer_value": "Selected historical-value baseline for 180-day repeat value.",
                "classification_macro_f1": "Held-out TF-IDF + logistic-regression macro-F1.",
                "experiment_power": "SKU-level, eight-week outcomes including zero-sales weeks.",
            },
        },
        **core,
    }


def validate_snapshot(snapshot: dict, *, require_full_dataset: bool = True) -> None:
    """Validate contracts, approved findings, privacy boundaries and fingerprint."""
    core = {key: snapshot[key] for key in ("metadata", "filtered", "fixed", "opportunities")}
    actual_fingerprint = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if actual_fingerprint != snapshot["analytical_fingerprint_sha256"]:
        raise ValueError("Static snapshot analytical fingerprint does not match its contents.")

    full = snapshot["filtered"][_selection_key(None, None)]["overview"]["kpis"]
    experiment = snapshot["fixed"]["experiment_summary"]
    classification = snapshot["fixed"]["classification"]
    clv = snapshot["fixed"]["clv"]
    if abs(full["net_revenue"] - (full["gross_revenue"] + full["cancellations"])) > 0.01:
        raise ValueError("Static net revenue does not reconcile to gross sales plus cancellations.")
    if abs(full["gross_sales_aov"] - full["gross_revenue"] / full["sale_invoices"]) > 0.005:
        raise ValueError("Static gross sales AOV does not reconcile.")
    if clv["winner"] != "Baseline (historical avg value)":
        raise ValueError("The approved customer-value baseline is not selected.")
    if min(bin_["lower"] for bin_ in clv["distribution"]) < 0:
        raise ValueError("Negative customer-value output found in the public aggregate.")
    if experiment["adequately_powered"] is not False:
        raise ValueError("The public demo must not claim the proposed experiment is powered.")

    if require_full_dataset:
        con = queries.connect()
        try:
            source_rows = int(con.execute("select count(*) from stg_transactions").fetchone()[0])
            retained_rows = int(con.execute("select count(*) from fct_order_lines").fetchone()[0])
        finally:
            con.close()
        actual = {
            "source_transactions": source_rows,
            "retained_transactions": retained_rows,
            "net_revenue": round(full["net_revenue"], 2),
            "sale_invoices": full["sale_invoices"],
            "cancellation_invoices": full["cancellation_invoices"],
            "gross_sales_aov": round(full["gross_sales_aov"], 2),
            "classification_macro_f1": round(classification["metrics"][0]["macro_f1"], 3),
            "available_products_per_arm": experiment["available_products_per_arm"],
            "required_products_per_arm": experiment["required_products_per_arm"],
        }
        if actual != EXPECTED:
            raise ValueError(f"B4 analytical regression mismatch: {actual!r}")

    raw = json.dumps(snapshot, sort_keys=True)
    forbidden_fragments = (
        '"customer_key"',
        '"customer_id"',
        '"invoice_no"',
        '"source_row"',
        '"email"',
        '"phone"',
        '"address"',
        "/Users/",
        "data/warehouse",
        ".duckdb",
    )
    found = [fragment for fragment in forbidden_fragments if fragment in raw]
    if found:
        raise ValueError(f"Sensitive or internal content found in static snapshot: {found}")


def write_snapshot(path: Path, snapshot: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("web/public/data/portfolio-demo.json"),
    )
    parser.add_argument(
        "--allow-non-production-data",
        action="store_true",
        help="Skip B4 full-dataset regression values (for the committed CI sample only).",
    )
    args = parser.parse_args()
    snapshot = build_snapshot()
    validate_snapshot(snapshot, require_full_dataset=not args.allow_non_production_data)
    write_snapshot(args.output, snapshot)
    print(
        f"Wrote {args.output} ({args.output.stat().st_size:,} bytes, "
        f"fingerprint {snapshot['analytical_fingerprint_sha256']})"
    )


if __name__ == "__main__":
    main()
