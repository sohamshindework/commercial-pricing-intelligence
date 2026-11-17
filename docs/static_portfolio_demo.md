# Verified static portfolio demo

## Architecture and provenance

`scripts/export_static_demo.py` reads the validated full warehouse and analytical
exports through the existing FastAPI contracts. It materialises only the responses
needed by the five React routes in `web/public/data/portfolio-demo.json`. Vite's
`demo` mode selects that snapshot; the normal build continues to use FastAPI.

The source is UCI Online Retail II (CC BY 4.0), covering 2009-12-01 to 2011-12-09.
The snapshot records 1,067,371 source lines and 1,033,062 retained product lines.
It is historical, single-retailer evidence for an independent portfolio analysis,
not a current market benchmark.

## Published data contract

| UI output | Pipeline source | Definition / limitation |
|---|---|---|
| Revenue KPIs and trend | DuckDB `fct_order_lines` via reporting queries | Net revenue includes credit-note value; sale and cancellation invoices are distinct measures. |
| Gross sales AOV | Same filtered fact scope | Gross product sales / distinct sale invoices. It is not net revenue / all invoices. |
| Market and family filters | Exact precomputed API responses for every market/family combination | Exact within the snapshot; both filters can be combined. |
| Product table | Aggregated product performance for every market/family combination | Product-level aggregates only; no invoice or customer detail. Pagination is applied in the browser. |
| Revenue bridges | Validated M2 exports | Fixed Jan–Nov comparison; descriptive attribution, not causal price effect. |
| Customer segments, cohorts and value | Validated M3 exports | Identified customers only; fixed full-history/holdout periods. Customer-value baseline is selected out of sample. |
| Product classification | Validated M4 held-out evaluation | TF-IDF + logistic regression; macro-F1 0.873. The withdrawn LLM score is not published as evidence. |
| Pricing opportunities | Validated measured gaps plus 231 precomputed capture scenarios | Scenario ranges, not realised uplift, causal impact or measured profit. |
| Price response and dispersion | Validated M5 exports | Observational associations; not elasticities. |
| Experiment sizing | Validated M5 SKU-level power results | Includes zero-sales weeks; 1,713 available vs 21,102 required SKUs/arm for a 5% MDE. |
| Executive decisions | Templated memo outputs | Recommendations and suggested owners, not commitments or realised outcomes. |

Arbitrary date filtering is deliberately disabled in demo mode. Publishing enough
detail for all possible date ranges would materially increase disclosure and is not
needed to demonstrate the analysis. The full local application retains date filters.

## Determinism and validation

The exporter sorts JSON keys and includes a SHA-256 fingerprint over the analytical
payload. It fails unless the full-data B4 regression values match. Tests independently
check revenue/AOV identities, every filter selection, model and power conclusions,
byte-level reproducibility, invalid static inputs and sensitive-field exclusion.

Regenerate and verify:

```bash
python scripts/export_static_demo.py
cd web && npm ci && npm run build:demo
cd .. && python scripts/check_static_artifact.py web/dist
```

## Public exclusions

The deployable artifact must not contain customer records or identifiers, invoice
identifiers, transaction rows, raw XLSX/ZIP archives, CSV/Parquet analytical exports,
DuckDB files, secrets, absolute local paths or backend origins. It uses system fonts
and contains no analytics or tracking integration.

## Hosting procedure (not executed in B5)

Use `web/` as the Vercel project root. `vercel.json` selects `npm run build:demo`,
serves `dist/`, provides SPA rewrites for refresh-safe React routes, revalidates the
snapshot and caches content-hashed assets immutably. Before publication, confirm
publication authority, retain UCI attribution, resolve the repository's missing
standalone licence file and repeat the full clean build, tests, artifact scan and
desktop/mobile browser review.
