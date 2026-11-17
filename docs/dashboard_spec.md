# Dashboard specification (6 pages)

Build these pages by hand in Power BI Desktop (and they mirror the React web
app). Every visual lists its **fields**, **measures** and **filters**. Measures
are defined in [`powerbi/dax/measures.dax`](../powerbi/dax/measures.dax). Slicers
marked *(global)* sit on every page.

**Global slicers:** `dim_date[year_month]` (timeline), `dim_country[market]`
(UK / International / Unknown), `dim_product[family]`.

**Footer (every page):** "Historical UCI Online Retail II data, 2009–2011, one UK
retailer — illustrates method, not current market facts. Revenue in GBP. No cost
data: margins are labelled scenarios. Observational price relationships are
associations, not causal."

---

## Page 1 — Executive summary

| Visual | Type | Fields / Measures | Filters |
|---|---|---|---|
| Net revenue | KPI card | `[Net Revenue]` | global |
| Revenue YoY % | KPI card | `[Revenue YoY %]` | global |
| Sale invoices | KPI card | `[Sale Invoices]` | global |
| Cancellation invoices | KPI card | `[Cancellation Invoices]` | global |
| Gross sales AOV | KPI card | `[Gross Sales AOV]` | global |
| Active customers | KPI card | `[Active Customers]` | global |
| Repeat rate | KPI card | `[Repeat Rate]` | global |
| Monthly net revenue | line | axis `dim_date[year_month]`, value `[Net Revenue]`; mark partial months | exclude `is_partial_month` optional |
| Revenue by family | bar | axis `dim_product[family]`, value `[Net Revenue]` | global |
| Top findings | text | key insights (catalogue churn, retention drop, price dispersion) | — |

## Page 2 — Revenue bridge

| Visual | Type | Fields / Measures | Filters |
|---|---|---|---|
| YoY waterfall (product lens) | waterfall | category `revenue_bridges[component]`, value `[Bridge Value]`; sort by `step_order` | `revenue_bridges[lens]="product"`, `[comparison]="yoy"` |
| Customer-change bridge | waterfall | same, `lens="customer"` | `comparison="yoy"` |
| Geography bridge | waterfall | same, `lens="geography"` | `comparison="yoy"` |
| Component table | table | `component`, `[Bridge Value]` | selected lens |
| Method note | text | "Price = ΔP·Q_current; descriptive, not causal." | — |

## Page 3 — Customers & cohorts

| Visual | Type | Fields / Measures | Filters |
|---|---|---|---|
| RFM segment sizes | bar | axis `rfm_customers[rfm_segment]`, value count | — |
| Segment value | bar | axis `rfm_segment`, value sum `monetary` | — |
| Cohort retention heatmap | matrix | rows `cohort_month`, cols `month_offset`, values retention % | — |
| Retention curve | line | axis `cohort_retention_curve[month_offset]`, value `[Avg Retention]` | — |
| CLV model vs baseline | table | from `clv_evaluation_metrics` (MAE, RMSE) | — |
| Predicted CLV | KPI / histogram | `[Avg Predicted CLV]`, dist of `expected_clv_horizon` | — |

## Page 4 — Products & families

| Visual | Type | Fields / Measures | Filters |
|---|---|---|---|
| Revenue by family | treemap | group `dim_product[family]`, value `[Net Revenue]` | global |
| Top products | table | `product_name`, `[Net Revenue]`, `[Units Sold]` | top N |
| Classification quality | table | `metrics_summary` (validated TF-IDF baseline accuracy, macro-F1) | — |
| Classification note | text | baseline chosen; former label-derived LLM result withdrawn | — |

## Page 5 — Pricing opportunities

| Visual | Type | Fields / Measures | Filters |
|---|---|---|---|
| Opportunity ranges | bar (low–high) | `opportunities[name]`, `[Opportunity Low]`..`[Opportunity High]` | — |
| Price dispersion | scatter/table | `price_dispersion_products` price_min/median/max, cv | min lines |
| Price–quantity association | bar | `price_response_by_family[within_slope]` with CI | — |
| Experiment sizing | cards | available/required SKUs per arm, adjusted MDE, duration and powered status (from experiment export) | — |
| Non-causal banner | text | "Associations only; ranges are scenarios; experiment validates." | — |

## Page 6 — Data notes & limitations

Text page: data source & licence (CC BY 4.0), cleaning rules summary
(link to `data_cleaning_rules.md`), the three hard limits (no cost → no margin;
observational ≠ causal; historical single-retailer data), missing-customer share
(~20% of revenue), partial-month handling, and the model-evaluation summary
(CLV vs baseline, validated classifier baseline). Include the revenue and duplicate-
treatment reconciliation notes. Never label all invoices as completed orders.
Use `duplicate_sensitivity` for the retain-versus-exclude comparison table.
