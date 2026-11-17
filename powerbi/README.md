# Power BI semantic model (TMDL) — build instructions

> **Status:** this repository ships the **semantic model and measures as text**
> (TMDL + DAX) plus the data exports. Power BI Desktop runs only on Windows, so
> the **report layout is built by hand** following
> [`docs/dashboard_spec.md`](../docs/dashboard_spec.md). No `.pbix` is committed
> and none is claimed. The accessible, working demo is the React web app
> (`web/`). Build this model on a Windows machine to produce the Power BI version.

## What is here

```
powerbi/
├── model/
│   ├── database.tmdl              compatibility level
│   ├── model.tmdl                 model settings, ExportFolder parameter, relationships
│   └── tables/                    one TMDL per table (columns, data types, measures, M partition)
└── dax/measures.dax               all DAX measures (also embedded in fct_order_lines.tmdl)
```

## Build steps (Windows, Power BI Desktop)

1. Run the pipeline so the exports exist:
   ```
   python scripts/build_marts.py
   python scripts/run_revenue.py
   python scripts/run_customers.py
   python scripts/run_products.py
   python scripts/run_pricing.py
   python scripts/export_powerbi.py
   ```
2. Create a new **PBIP** project in Power BI Desktop (Preview: *Power BI Project
   (.pbip) save format* must be enabled).
3. Replace the generated `…/<name>.SemanticModel/definition/` TMDL with the files
   under `powerbi/model/` (or copy the tables and measures in via the TMDL view /
   external tools such as Tabular Editor).
4. Set the **ExportFolder** parameter (model.tmdl) to your local
   `data/exports/powerbi/` path (keep the trailing `\`).
5. Also import the pre-computed analytics tables the measures reference — each is
   a Parquet file loaded the same way (`Parquet.Document(File.Contents(…))`):
   | Table in model | Source file |
   |---|---|
   | `revenue_bridges` | `data/exports/revenue/bridges.parquet` |
   | `monthly_revenue` | `data/exports/revenue/monthly.parquet` |
   | `clv_customers` | `data/exports/customers/clv_customers.parquet` |
   | `cohort_retention_curve` | `data/exports/customers/retention_curve.parquet` |
   | `opportunities` | `data/exports/pricing/opportunities.parquet` |
6. Mark `dim_date` as the **date table** (already annotated) and check the four
   star relationships (model.tmdl).
7. Build the six report pages from `docs/dashboard_spec.md`.

## Refresh

The model imports from the local Parquet exports. To refresh: re-run the pipeline
scripts above (they regenerate the exports) and press **Refresh** in Power BI
Desktop. For a published model, point the exports at a shared/OneDrive folder and
configure scheduled refresh on that folder.

## Reconciliation

The star-schema measures must reproduce
[`data/exports/powerbi/measures_reconciliation.csv`](../data/exports/powerbi/measures_reconciliation.csv)
(Net Revenue, Gross Revenue, Cancellations, Sale Invoices, Cancellation Invoices,
Gross Sales AOV, Active Customers, Units Sold). Put the Python-vs-DAX
comparison table in the project README once the model is loaded on Windows.

## Why analytics are imported, not re-computed in DAX

Price/volume/mix decomposition, CLV (BG/NBD + Gamma-Gamma) and cohort retention
are implemented once, in Python, and validated by tests. Power BI **visualises the
exported results** rather than re-deriving them in DAX, so there is a single
source of truth for the business logic.
