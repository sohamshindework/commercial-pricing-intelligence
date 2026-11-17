# SPEC: Commercial & Pricing Intelligence

Build specification for the project. Work milestone by milestone and stop after each
one for review.

---

## 1. Business problem

An online retailer's commercial team needs answers to five questions:
1. **Why did revenue change?** Split year-on-year change into price, volume, mix, new/lost customers, and new/discontinued products.
2. **Which customers matter and are we keeping them?** Segments, cohort retention and customer lifetime value.
3. **Which products drive the business, and in which product families?** The data has no category field, so it must be created.
4. **Where might pricing be improved?** Identify candidates, give *ranges* of possible impact, and design an experiment to test them.
5. **What should we do next?** A ranked list of opportunities, a KPI tree and a short product requirements document (PRD) for a pricing-test capability.

**Audience:** commercial director, pricing manager, CRM manager, category manager.

**Deliverables:**
- a reproducible analytics pipeline;
- a SQL data mart;
- a Power BI dashboard;
- a commercial memo (max 4 pages);
- an experiment design;
- a PRD;
- a model-evaluation report.

## 2. Data

**UCI Online Retail II**
- Real transactions of a UK online gift retailer, Dec 2009 – Dec 2011, about 1.07m rows.
- Licence: CC BY 4.0. Credit the dataset and authors in the README.
- Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii (download script; do not commit the raw file).
- Fields: Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country.

**Known traps that must be handled and documented:**
- cancellations (Invoice starting "C") and negative quantities;
- non-product codes (POST, DOT, M, BANK CHARGES, AMAZONFEE, test codes);
- missing Customer ID (about 20–25%);
- zero or negative prices and extreme outliers;
- duplicate rows;
- the same StockCode with different descriptions;
- partial months at the edges of the data;
- revenue is in GBP.

**Hard limits (must appear in the README, the memo and the dashboard footer):**
- **No cost data → no margin.** Margin views are scenario-based only and labelled "assumed cost ratio".
- **Observational price variation is not causal.** Price-response estimates are descriptive, shown as ranges, and the memo says so. Causal claims require the proposed experiment.
- The data is from 2009–2011 and from one UK retailer. Findings illustrate the method; they are not current market facts.

## 3. Tech stack

| Concern | Choice |
|---|---|
| Language | Python 3.11+ |
| Pipeline and SQL | **DuckDB** + SQL files in `sql/` (staging → cleaned → star schema), run by a Python runner. dbt-duckdb is optional, only if it stays simple |
| Analysis | pandas, NumPy, SciPy, statsmodels |
| ML | scikit-learn; `lifetimes` (or PyMC-Marketing) for BG/NBD + Gamma-Gamma CLV, with a simple baseline |
| LLM | provider-agnostic client with record/replay (no key needed in tests/CI); Pydantic-validated structured output |
| Dashboard | **Power BI** (see §6). Python/Plotly charts for the memo |
| Excel | openpyxl: pricing-opportunity and experiment-sizing workbook |
| Docs | Markdown → PDF memo; Mermaid/BPMN not needed here |
| Tests | pytest + data tests (row counts, uniqueness, reconciliation) |
| CI | GitHub Actions on a 5% sample fixture committed to `tests/fixtures/` |

## 4. Milestones and acceptance criteria

### M1. Ingest, clean, model (SQL)
- `scripts/download.py` fetches and checksums the data.
- SQL layers:
  - `stg_` (raw typed);
  - `int_` (cleaning rules, each one documented);
  - marts: `fct_order_lines`, `dim_customer`, `dim_product`, `dim_date`, `dim_country`.
- A data-quality report lists rows removed by each rule.
- **Done when:** total cleaned revenue reconciles to raw minus documented exclusions (to the penny), and tests check keys are unique and not null.

### M2. Revenue decomposition
- Year-on-year and month-on-month price/volume/mix bridge at product level. New/lost products and new/lost/returning customers are separate bars. State the method (e.g., price effect = ΔP × Q_current).
- Country and channel view (UK vs international).
- **Done when:** the bridge components sum exactly to total change (a test asserts this), and a waterfall chart exists.

### M3. Customers: segmentation, retention, CLV
- RFM segmentation with readable business labels, plus k-means (or a Gaussian mixture) on scaled RFM. Report silhouette and segment stability across 2 time windows; choose the simpler method if it is just as good.
- Cohort retention matrix (monthly).
- CLV: BG/NBD + Gamma-Gamma, compared with a naive baseline (historical average). Use a **time-based holdout**: calibrate on the first ~18 months, test on the last ~6. Report MAE and calibration plots for predicted vs actual purchases.
- **Done when:** the evaluation table exists, and the memo uses CLV only if it beats the baseline. Otherwise it says so.

### M4. Product families: LLM classification vs baseline
- Hand-label about 300 products into 10–15 families. Document the labelling guide and split 150 dev / 150 test.
- Baseline: keyword rules or TF-IDF + logistic regression.
- LLM: structured output, families fixed to the taxonomy, with an "other/unsure" option; batch processing, caching, cost and latency logged.
- Report accuracy, macro-F1 and a confusion matrix on the **test set only**.
- **Done when:** the better method is used for the full catalogue and the choice is justified with numbers. If the baseline wins, use the baseline and say so.

### M5. Pricing opportunities and experiment design
- Price-dispersion analysis: the same product sold at different unit prices over time (e.g., list price vs quantity tiers).
- Descriptive log-log price response by family, with confidence intervals. Clearly labelled non-causal; flag confounders (seasonality, quantity tiers, customer type).
- Opportunity list: candidate actions (e.g., quantity-break redesign, minimum-order threshold, price on long-tail items) with **revenue impact as a range under stated assumptions** and margin as a scenario only.
- Experiment design for the top opportunity:
  - hypothesis;
  - unit of randomisation;
  - primary and guardrail metrics;
  - power calculation (minimum detectable effect, sample size, duration, from the data's variance);
  - risks such as contamination and novelty effects;
  - decision rule.
- An Excel sizing workbook with live formulas.
- **Done when:** no output states a causal elasticity, and a test checks the power calculation against statsmodels.

### M6. Power BI dashboard
- Export the marts to Parquet/CSV for Power BI. Provide a **Power BI Project (PBIP) with the TMDL semantic model**: star-schema relationships, a date table and DAX measures (revenue, orders, AOV, active customers, retention %, repeat rate, CLV, PVM components, YoY %).
- Pages:
  1. Executive summary
  2. Revenue bridge
  3. Customers and cohorts
  4. Products and families
  5. Pricing opportunities
  6. Data notes and limitations
- `docs/dashboard_spec.md` lists every visual, field, measure and filter, so the layout can be built in Power BI Desktop.
- **Done when:** the semantic model loads in Power BI Desktop, measures match the Python results (reconciliation table in the README), and screenshots are in the README.

### M7. Commercial memo, KPI tree, PRD
- Memo (max 4 pages):
  - answer first;
  - 3–5 recommendations with impact ranges;
  - what we do *not* know (cost, causality, data age);
  - next steps.
- KPI tree: revenue → customers × orders per customer × AOV → units × price.
- PRD: "Pricing experimentation capability". Covers problem, users, requirements, metrics, risks and rollout.
- **Done when:** every number in the memo is generated from the pipeline (templated) and checked by a test.

### M8. Polish
- README:
  - pitch;
  - screenshots;
  - architecture;
  - quick start;
  - model-evaluation table;
  - limitations;
  - data credit;
  - "How this was built".
- Fresh-clone install verified.

## 5. Integrity rules
- Never present scenario margins, descriptive elasticities or simulated numbers as facts.
- Never claim the retailer, or any named company, is a client. It is a public dataset.
- Report model results on held-out data only. No tuning on the test set.
- If a method fails to beat its baseline, keep the baseline and report it. That is a finding, not a failure.

## 6. Power BI note
Power BI Desktop runs only on Windows. A coding agent can write the data exports, the PBIP/TMDL semantic model and the DAX measures as text files. The report layout must be built and checked by hand in Power BI Desktop (Windows PC or VM) using `docs/dashboard_spec.md`. If Windows is not available, build the same pages in Streamlit and say so; do not claim Power BI.

## 7. Definition of done
- [ ] All milestone checks pass; pytest is green; CI runs on the sample fixture.
- [ ] Revenue reconciles and the bridge sums exactly.
- [ ] The CLV and classification evaluations are published, with their baselines.
- [ ] The experiment design includes a validated power calculation.
- [ ] Power BI screenshots and a measure reconciliation table are in the README.
- [ ] The memo, KPI tree and PRD are generated from the pipeline numbers.
- [ ] Limitations appear in the README, the memo and the dashboard.
