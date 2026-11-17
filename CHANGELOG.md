# Changelog

## Stage B5.1 dependency security and publication readiness — 2026-11-17

- Removed the Tailwind 3 file-watcher/glob advisory chain by migrating the build-only
  integration to Tailwind 4.3.5 and `@tailwindcss/postcss` 4.3.5, with the same retained
  design configuration.
- Updated React Router from 6.30.6 to 7.18.5, eliminating both production dependency
  advisories without changing the five-route application structure.
- Evaluated the remaining `picomatch` CVE-2026-112366 chain. All published versions are
  affected and upstream lists no patch. Remaining uses are development-only, accept only
  trusted repository globs and are absent from the static artifact; the full audit remains
  unsuppressed pending an upstream release or explicit owner risk acceptance.
- Added a publication-readiness assessment and public in-app UCI DOI / CC BY 4.0
  attribution. No licence, publication, deployment, commit or push was performed.

## Stage B5 verified static portfolio demo — 2026-11-17

- Added a deterministic build-time exporter for a 6.49 MB aggregate-only portfolio
  snapshot. It exercises the existing FastAPI contracts, validates the B4 analytical
  regressions and publishes no customer records, invoice identifiers or transaction rows.
- Added an explicit Vite demo mode. All five routes run without FastAPI or DuckDB;
  market/family filters, product pagination, decomposition lenses and precomputed pricing
  scenarios remain functional. Date inputs are visibly disabled because the privacy-safe
  snapshot cannot reproduce arbitrary date slices faithfully.
- Added static-data, reconciliation, reproducibility and deployable-artifact privacy tests,
  plus a Vercel SPA configuration and clean demo build gate. No deployment, publication,
  commit or licence change was made.

## Stage B2 revenue and transaction integrity correction — 2026-11-16

- Replaced the ambiguous 46,922 “orders” / GBP 403.38 AOV with explicit invoice
  semantics: 39,516 sale invoices, 7,406 cancellation invoices, and gross sales
  AOV = gross product sales / sale invoices. Cancellation value remains in net revenue.
- Preserved the independently proven 22,523-row source-sheet overlap removal. Reclassified
  same-sheet exact-looking rows as unresolved rather than proven duplicates: 11,790 product
  lines are now retained and flagged. Net revenue changes from GBP 18,927,399.07 under the
  exclusion sensitivity to GBP 18,981,261.52 under the chosen retain policy; gross sales AOV
  changes from GBP 497.11 to GBP 498.56. Both scenarios are exported and documented.
- Replaced product-week pseudoreplication in experiment power with SKU-level randomisation
  and analysis. Eight-week SKU outcomes include zero-sales weeks; historical pre-period
  adjustment is explicit. The 5% target requires 21,102 SKUs per arm versus 1,713 available;
  the adjusted MDE with the available catalogue is 17.6%, so the 5% test is not powered.
- Rebuilt all downstream artifacts. The Stage B1 conclusions remain: TF-IDF macro-F1 is
  0.873; the historical-value customer baseline still wins (MAE GBP 633.45 versus GBP 644.46
  for BG/NBD + Gamma-Gamma), with no negative or non-finite exported values.

## Stage B1 integrity correction — 2026-11-16

- Withdrew the former LLM macro-F1 result: its replay cassette was derived from
  gold labels and was not an independent evaluation. TF-IDF + logistic regression
  is now the sole selected classifier (held-out macro-F1 0.873).
- Replaced purchase-count-only CLV selection with complete held-out customer-value
  evaluation in GBP. BG/NBD + Gamma-Gamma does not beat the historical-value
  baseline (MAE GBP 642.24 vs 631.22), so forward scores use the baseline.
- Restricted Gamma-Gamma to eligible repeat customers and eliminated negative and
  non-finite customer-value scores. This section supersedes older M3/M4 result notes.

Milestone-by-milestone progress (see `SPEC.md`).

## Frontend — consolidated to four pages
- Folded **Executive Decisions into the Commercial Overview**: extracted a reusable
  `RecommendedActions` component (recommendation cards with confidence badges, CSV
  export, "what we do not know") and render it at the foot of the Overview, which
  already leads with an answer-first summary. Removed the separate Executive page,
  its route and nav entry (nav is now four items), and the stale screenshot. README
  updated to four pages. Backend `/api/executive/summary` is unchanged and still
  feeds the folded section. Checks stay green: Python 113 + ruff; frontend
  typecheck/lint clean, 6 Vitest tests, build succeeds.

## Frontend modernization — Phase F (final integration & QA)
- **Retired the Streamlit UI** now that React has parity: removed `app/`, the Streamlit
  theme module (`reporting/theme.py`), the app-compile test, the old Streamlit
  screenshots, and the `[app]` (streamlit/plotly) extra. The analytical code stays —
  `reporting.exports` powers the FastAPI backend. Scrubbed Streamlit references from
  docs, source comments and the editor launch configuration.
- **Professional README** with the pitch, real screenshots, a React→FastAPI→Python→DuckDB
  (+ Power BI) Mermaid architecture, methodology with honest results, Power BI/Excel
  deliverables described accurately (text model, no `.pbix`), quick-start, testing,
  limitations, dataset credit and author attribution.
- **Frontend CI:** added a `web` job (npm ci, type-check, lint, Vitest, production build)
  alongside the Python job; committed `web/package-lock.json`.
- **Fresh end-to-end verification:** the full pipeline rebuilds from the warehouse
  (`build_marts` → revenue → customers → products → pricing → export_powerbi → memo),
  the API boots and reconciles (overview net revenue £18,927,399.07), and every check
  passes — Python 113 + ruff clean; frontend type-check/lint clean, 6 Vitest tests,
  build succeeds. Power BI and Excel untouched; nothing committed or deployed.

## Frontend modernization — Phase E (Executive Decisions page)
- **Backend:** `reporting.memo.executive_summary()` assembles prioritised, evidence-linked
  recommendations, monitoring KPIs and limitations from the same templated memo numbers
  (no hand-typed business results). New `/api/executive/summary` endpoint + test (29 API
  tests total).
- **Frontend:** the final page — a headline (net revenue, YoY), three prioritised
  recommendation cards (action, evidence, correctly-labelled *hypothetical* impact,
  success metric, confidence), a monitoring-KPI list, a "what we do not know" panel, and
  a working **CSV export** of the recommendations (built from the API response). All five
  pages are now live on real data; the honest scaffolds are gone (`Scaffold.tsx` removed).
- Verified live. Checks: Python 114 pass + ruff clean; frontend typecheck + eslint clean,
  6 Vitest tests, build succeeds. Streamlit/Power BI/Excel untouched; nothing committed.
  Remaining: Phase F (final QA, README/screenshots, retire Streamlit).
- **Refinement:** added an answer-first **Situation** synthesis and richer headline
  (net revenue, YoY, orders, active customers) to the Executive page — all from the
  templated memo numbers — and turned the confidence level into a scannable colour-coded
  **badge** per recommendation. Checks stay green.

## Frontend modernization — Phase D (Customer Analytics & Pricing pages)
- **Backend:** new `customers`, `pricing` and `experiments` routers. Endpoints:
  `/api/customers/{segments,cohorts,clv}`, `/api/pricing/{opportunities,dispersion,
  price-response}`, `/api/experiments/{summary,power-curve}`. Opportunities take
  scenario **capture inputs** and recompute ranges = measured gap × capture (gap is
  fixed; capture is a stated assumption — never a causal/profit claim). The power
  curve is computed with statsmodels from the real metric variance. All model
  outputs are flagged fixed-period. 7 new API tests (28 total).
- **Frontend:** new `CohortHeatmap` (retention triangle, light-lilac→iris scale) and
  `RangeInput` slider. **Customer Analytics** page: RFM segments, cohort heatmap +
  average-retention curve, CLV evaluation (model vs baseline MAE/RMSE, chosen model,
  predicted-value distribution) — with a clear note that these are full-history model
  outputs and the global filters don't apply. **Pricing & Experiments** page:
  opportunities with **live capture sliders** (verified recomputing from the API),
  price–quantity association by family (non-causal), a price-dispersion table, and
  experiment sizing with a **power curve** (MDE vs sample size). A warning-accented
  banner keeps observation, scenario and causal validation separate.
- Verified live (cohort heatmap, slider recompute, power curve). Checks: Python 113
  pass + ruff clean; frontend typecheck + eslint clean, 6 Vitest tests, build succeeds.
  Streamlit/Power BI/Excel untouched; nothing committed. Only Executive Decisions
  remains a scaffold (Phase E).

## Frontend modernization — Phase C.1 (Revenue & Products refinements)
- **Decomposition lens toggle** (Product / Customer / Geography) on the revenue-drivers
  waterfall via a new reusable `Segmented` control — the customer and geography bridges
  were already served by the API; now they are explorable. Note text updates per lens.
- **Skeleton loaders** (`ChartSkeleton` / `BarsSkeleton` / `TableSkeleton`) replace the
  plain spinner on both the Revenue & Products and Overview charts for a smoother load.
- **Revenue by market** now shows share-of-selection (tooltip + a one-line caption) and
  a height that fits the number of markets instead of wasting space.
- **Graceful single-family state:** filtering to one family shows a clear note instead of
  a redundant one-bar category chart; per-class classification bars now surface the test
  **support count** in the tooltip, with a note that low-support classes have noisier F1.
- Verified live (lens toggle switches the waterfall to the customer decomposition).
  Checks: Python 106 pass + ruff clean; frontend typecheck + eslint clean, 6 Vitest tests,
  build succeeds.

## Frontend modernization — Phase C (Revenue & Products page)
- **Backend:** added `/api/revenue/by-market` (filtered) and `/api/products/classification`
  (fixed-period, from the M4 test-set exports); `queries.revenue_by_market` reuses the
  shared `_scope`; metadata now returns family display names. 4 new API tests (18 total):
  by-market sums to the overview total, family filter correctness, classification fixed-period.
- **Frontend:** new reusable `RankedBars` chart and a typed `DataTable` + `Pagination`.
  Built the full **Revenue & Products** page on real data: revenue-drivers waterfall
  (fixed period, non-causal note), revenue by market, category contribution by family,
  a **server-paginated** product-performance table (1–10 of 4,739, Previous/Next), and
  product-classification quality (baseline vs LLM metrics + per-class F1) with the
  lineage caveat. All respond to the global filters except the clearly-labelled
  fixed-period panels.
- Verified live (desktop + mobile), pagination interaction confirmed against the API.
  Checks: Python 106 pass + ruff clean; frontend typecheck + eslint clean, 6 Vitest
  tests, production build succeeds. Streamlit/Power BI/Excel untouched; nothing committed.

## Frontend modernization — Phase B.1 (visual design & UI quality)
- **Final palette** applied (canvas `#F7F4F0`, iris `#6653A3`, lilac, coral, sage,
  plum ink) across Tailwind tokens; chart tokens centralized in `charts/chartTheme.ts`
  with consistent semantic mapping (positive=growth, coral=opportunity, sage=customer).
- **Reusable chart system:** `TrendLine` (area trend with gradient + shared tooltip),
  `Waterfall` (true running-cumulative revenue bridge), `ChartTooltip` — built for
  reuse in later phases, not all dumped on the Overview.
- **Overview recomposed into a deliberate hierarchy:** a performance-summary band
  (narrative from real bridge data), a primary net-revenue figure with supporting
  orders/AOV (replacing six equal cards), one dominant monthly-revenue chart, a
  revenue-drivers waterfall beside ranked commercial findings, compact customer-
  coverage stats, and "go deeper" links — instead of a generic card grid.
- **Shell:** slimmer branded sidebar with a clear active-state indicator and a single
  identity placement; header no longer repeats the project name.
- **Copy:** removed developer-voice strings ("responds to the filters above",
  "fixed comparison period, not affected by filters") for business language
  ("Monthly revenue", "Revenue drivers", "Comparison: Jan–Nov 2011 vs Jan–Nov 2010",
  "Customer coverage"); the non-causal caveat is kept, phrased naturally.
- **Verified at 1440 / 1024 / 768 / 390** with screenshots; fixed two defects found
  (KPI overlap on tablet → stack until `lg`; trend Y-axis mixed £m/£k units →
  consistent millions). No horizontal overflow at any width.
- Checks: Python 102 pass + ruff clean; frontend typecheck + eslint clean, 4 Vitest
  tests, production build succeeds. Streamlit, Power BI and Excel untouched; nothing
  committed or deployed. Updated `assets/screenshots/react_overview.jpg`.

## Frontend modernization — Phase B (React + FastAPI foundation)
- **Backend query layer** `reporting/queries.py`: parameterized, read-only DuckDB
  aggregates for interactive filtering (date range, market, family) with one
  centralized net-revenue definition (`NET_REVENUE`) that matches the marts/DAX.
  Fixed-period analytics still come from `reporting/exports.py`.
- **FastAPI app** (`api/`): Pydantic schemas, routers (metadata, overview,
  revenue trend/by-family, products), input validation (market enum, date order,
  pagination bounds), a 503 when the warehouse is absent, CORS for the dev client,
  and OpenAPI docs. The YoY bridge is served fixed-period and flagged
  `interactive: false` so global filters never appear to change it.
- **React + TypeScript + Vite** (`web/`): premium design system (ivory/iris/
  lavender/terracotta, Plus Jakarta Sans + DM Sans, tabular numerals) in Tailwind;
  app shell + responsive nav, 5-page routing, shared components (KpiCard, Card/
  ChartCard, PageHeader, FilterBar, loading/empty/error states), global filter
  context, typed API client + TanStack Query hooks. **Overview page is live on
  real data** (KPIs, revenue trend, YoY decomposition); the other four pages are
  honest scaffolds (no fabricated figures) for Phases C–E.
- **Checks:** 102 Python tests pass (10 new FastAPI TestClient tests — reconciles
  to marts, filter correctness, validation, pagination), ruff clean; frontend
  typecheck + eslint clean, 4 Vitest tests, production build succeeds. Verified
  the full stack (React → FastAPI → DuckDB) rendering live; screenshot in
  `assets/screenshots/react_overview.jpg`.
- Streamlit, Power BI (TMDL/DAX) and Excel are **untouched** and remain available.
  Optional deps: new `[api]` extra (fastapi, uvicorn, httpx); `web/` deps are npm.

## M7 — Commercial memo, KPI tree, PRD
- Added `commercial_intelligence.reporting.memo`: `memo_numbers()` pulls every
  figure from the validated exports, and `render_memo` / `render_kpi_tree` /
  `render_prd` template them — **no number is hand-typed**. `scripts/run_memo.py`
  writes `docs/commercial_memo.md`, `docs/kpi_tree.md`,
  `docs/prd_pricing_experimentation.md`.
- **Memo (≤4 pages):** answer-first (YoY +2.3%, carried by new products vs a
  continuing-range volume decline), what moved revenue (PVM + customer lenses),
  5 recommendations with scenario ranges, an explicit "what we do NOT know"
  (cost, causality, data age), and sized next steps.
- **KPI tree:** revenue = customers × orders/customer × AOV and gross = units ×
  avg unit price, with live numbers that tie out.
- **PRD** for the pricing-experimentation capability: problem, users,
  requirements, metrics, risks, rollout — reusing the M5 experiment numbers.
- Added `experiment_summary` to the M5 exports so the memo/PRD cite power numbers
  from a validated source.
- **Test (acceptance):** a CI-safe synthetic-exports fixture proves the key memo
  figures are templated from the exports (net revenue, orders, opportunity range,
  sample size, CLV MAE, classifier F1, retention), that the required sections and
  limitations are present, that the KPI identity ties, and that no placeholder or
  stray NaN leaks. 92 tests pass, ruff clean.

## M6 — Business intelligence (Power BI model + Streamlit app)
- **Power BI (text deliverables, Windows-only to build — no `.pbix` claimed):**
  `scripts/export_powerbi.py` exports the star schema + aggregates to
  `data/exports/powerbi/`; TMDL semantic model in `powerbi/model/` (tables,
  columns, relationships, marked date table, M partitions); all DAX measures in
  `powerbi/dax/measures.dax`; six-page `docs/dashboard_spec.md`;
  `docs/data_dictionary.md`; `powerbi/README.md` with build + refresh steps.
  Analytics (PVM, CLV, cohorts) are **imported** from Python exports, not
  re-computed in DAX — one source of truth.
- **Measure reconciliation:** `measures_reconciliation.csv` holds the Python KPI
  values the DAX must reproduce (net revenue £18.93m, orders 46,922, AOV £403.38,
  active customers 5,875, units 11.19m).
- **Streamlit app** (`app/`): 6 pages (Overview, Revenue Drivers, Customer
  Intelligence, Product Intelligence, Pricing Opportunities, Executive Decisions),
  light premium theme (ivory/slate/sage), reading only validated exports through
  `commercial_intelligence.reporting.exports` — **no business-logic duplication**.
  Launched and verified rendering end-to-end; screenshots in `assets/screenshots/`.
- Deps (optional `[app]` extra): streamlit, plotly. Tests: reporting loaders with
  synthetic exports (CI-safe), KPI math, missing-export error, warehouse
  reconciliation, and an app-source compile check. 87 tests pass, ruff clean.

## M5 — Pricing opportunities and experiment design
- Added `commercial_intelligence.pricing`: price dispersion (`dispersion.py`),
  descriptive non-causal price response (`price_response.py`), opportunity sizing
  (`opportunities.py`), experiment design + power (`experiment.py`), Excel sizing
  workbook (`workbook.py`), report (`report.py`). `scripts/run_pricing.py` runs it.
- **Dispersion:** ~99% of products with enough history sell at more than one unit
  price; a robust median-based price-realisation gap of ~GBP 2.3m is the raw
  material for the opportunities.
- **Price response:** per-family log-log association, pooled vs **within-product**
  (product fixed effects) with HC1 95% CIs. All slopes strongly negative (bulk
  discounting) — reported as **associations, not elasticities**.
- **Opportunities:** price realisation (scenario range GBP 464k–1.16m, 2.5–6.1% of
  net revenue) and quantity-break discount-leakage, each separating
  observation / hypothesis / scenario / validation, with an assumptions register,
  confounders, and margin as a labelled *assumed cost ratio* scenario only.
- **Experiment:** SKU-randomised price-floor test — hypothesis, guardrails, risks,
  decision rule, and a **statsmodels power calculation** (≈39.6k product-weeks/arm
  for a 5% MDE on a noisy metric; MDE round-trips to 5.0%). Live-formula Excel
  workbook at `excel/experiment_sizing.xlsx`.
- **Integrity guard:** the report render asserts no bare price-elasticity/causal
  claim (disclaimers required); a test checks the power calc against statsmodels
  and another rejects a bare elasticity claim. Dep added: statsmodels.

## M4 — Product-family classification (historical entry; corrected above)
- Added `commercial_intelligence.products`: taxonomy + Pydantic schema
  (`taxonomy.py`), TF-IDF + logistic-regression baseline (`baseline.py`),
  provider-agnostic LLM client with record/replay (`llm_client.py`), metrics
  (`evaluate.py`), full-catalogue labelling (`classify.py`), report (`report.py`).
  `scripts/run_products.py` runs it; `scripts/record_llm_cassette.py` records the
  replay predictions.
- **Taxonomy:** 13 families incl. explicit *Other / Unsure*
  (`data/labels/taxonomy.csv`). **Gold:** 300 best-sellers hand-labelled by the
  author (`data/labels/product_families_gold.csv`), stratified 153 dev / 147 test;
  labelling guide in `docs/product_labeling_guide.md`.
- **Corrected result:** the independently evaluated TF-IDF baseline achieved test
  accuracy 0.891 and macro-F1 0.873. The former LLM score and selection are
  withdrawn because the replay cassette was derived from the gold labels. The
  catalogue is now labelled by the baseline only; LLM replay is disabled.
- **Historical implementation note:** a provider-agnostic record/replay client was
  built, but its old cassette is quarantined and is not an admissible evaluation
  or catalogue-labelling source.
- Deps added: scikit-learn, pydantic. Tests: gold integrity, stratification,
  schema coercion, baseline determinism, keyless replay, missing-cassette error,
  metrics, and an end-to-end pipeline run on the fixture warehouse.

## M3 — Customer intelligence
- Added `commercial_intelligence.customers`: RFM + k-means segmentation
  (`segmentation.py`), monthly cohort retention (`cohorts.py`), CLV with a
  leakage-free holdout (`clv.py`), memo plots (`plots.py`), report/exports
  (`report.py`). `scripts/run_customers.py` runs it all. Identified customers only.
- **Segmentation:** RFM quintiles mapped to the classic business grid; k-means on
  scaled log-RFM with k chosen by silhouette (**k=3**, silhouette 0.40) and
  stability measured by Adjusted Rand Index across two time windows (ARI≈0.17 →
  recommend the transparent RFM grid operationally, k-means as a cross-check).
  RFM scoring made order-independent (deterministic SQL + rank).
- **Cohort retention:** monthly first-purchase cohorts; month-1 repeat ≈21%, then
  flat — a retention, not acquisition, problem. Heatmap in `assets/customers/`.
- **Customer value (corrected above):** a time-based holdout separately diagnoses
  purchase counts, but operational selection is based on complete held-out value
  in GBP. BG/NBD + Gamma-Gamma has MAE £642.24 versus £631.22 for the historical-
  value baseline, so the baseline is selected. Gamma-Gamma is applied only to
  eligible repeat buyers; all exported values are finite and non-negative.
- Exports in `data/exports/customers/` (9 tables) and `docs/m3_customer_intelligence.md`.
- Tests: a strict no-leakage test (extra holdout transactions change actuals only,
  never calibration features), baseline-formula identity, RFM range/label and
  recency-direction checks, k-means determinism, cohort invariants, reproducibility.
- **M3 review hardening:** verified RFM monetary reconciles to identified-customer
  net revenue (the £1,406 gap is exactly the 23 excluded cancellation-only
  customers) and all 125 RFM score combinations map to a label. Added a CLV
  **split-sensitivity** check (the historical-value baseline wins on complete value
  at every tested calibration cut-off — 2011-03/05/07) and documented two caveats surfaced by the
  review: RFM Frequency-quintile tie-arbitrariness for single-purchase customers,
  and cohort right-censoring in late-tenure offsets.

## M2 — Revenue decomposition
- Added `commercial_intelligence.revenue`: pure decomposition arithmetic
  (`decomposition.py`), a warehouse-fed engine (`engine.py`) and findings/export
  rendering (`report.py`). `scripts/run_revenue.py` builds everything.
- **Three independent, exactly-reconciling lenses** on the same net-revenue change,
  reported side by side (never merged, so mix and customer effects are not
  double-counted):
  - **Product price/volume/mix** on gross sales, plus new/discontinued-product
    and returns bars. An explicit residual closes any average-price rounding dust.
  - **Customer change** (new / lost / retained / guest) — exact to the penny.
  - **Geography** (UK / International / Unknown) — exact to the penny.
- Comparison window: **Jan–Nov 2011 vs Jan–Nov 2010** (11 complete months; Dec 2009
  isolated and Dec 2011 partial are excluded). Configurable in `config/settings.toml`.
- Primary result: net revenue **+GBP 195,090 (+2.3%)**; growth driven by new
  products (+2.04m) offsetting a continuing-catalogue volume decline (−1.44m).
- Exports (`data/exports/revenue/`: `bridges`, `monthly` as Parquet + CSV) and
  `docs/m2_revenue_decomposition.md` for the memo, Power BI and Streamlit.
- Tests: hand-computed unit tests for every component (price/volume/mix, new,
  discontinued, zero-quantity, returns, customer, guest, geography) and
  fixture-level reconciliation identities for all three lenses.
- M1 audit before M2: confirmed overlap removal is proven row-for-row, R02
  duplicates are immaterial double-postings (~0.3% of revenue), and
  cancellation/missing-ID/net-revenue definitions are consistent. No changes needed.

## M1 — Ingest, clean, model
- DuckDB pipeline: landing Parquet → `stg_` → `int_` → star-schema marts
  (`fct_order_lines`, `dim_customer`, `dim_product`, `dim_date`, `dim_country`).
- `scripts/download.py` (checksum-verified), `scripts/build_marts.py`,
  `scripts/make_fixture.py` (committed 5% CI sample).
- Reconciles to the penny on the full 1.07m rows; data-quality report in
  `docs/`. 24 tests; CI on the fixture.
