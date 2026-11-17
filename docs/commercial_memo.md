# Commercial performance memo

_2026-11-16 · Audience: commercial director, pricing manager, CRM and category managers. Every figure is generated from the analytics pipeline._

## Answer first

Net revenue over the comparable window (Jan-Nov 2011 vs Jan-Nov 2010) is **+2.2%** year-on-year. The headline is healthy but the *composition* is the concern: growth is carried by **new products (£2,047,430)** while the continuing range lost volume (**−£1,452,782**), and **retained customers spent less (−£389,163)**. The business is refreshing its catalogue and customer base rather than deepening either. Total net revenue is **£18.98m** from **39,516 sale invoices** at a gross sales AOV of **£499**; **7,406 cancellation invoices** remain in net revenue.

## What moved revenue

- **Product price/volume/mix:** price −£140,937, volume −£1,452,782, mix £460,178; new products £2,047,430, discontinued −£664,300. (Descriptive attribution, not a causal price effect.)
- **Customers:** new £1,378,310, lost −£1,055,231, retained −£389,163. About **21%** of first-time buyers return the next month — retention, not acquisition, is the gap.

## Recommendations (impact as ranges, under stated assumptions)

1. **Price realisation on high-dispersion products.** A measured price-realisation gap of £2,327,994 supports a scenario uplift of **£465,599–£1,163,997** (2.5–6.1% of net revenue) if partially recovered without volume loss. Validate with the experiment below before acting.
2. **Shift investment toward first-90-day retention.** Repeat purchasing is weak; a retention programme targets the clearest structural gap. Frame as a measured test.
3. **Redesign quantity-break discounts** to stop deep discounts leaking to small line quantities (a smaller but clean governance win).
4. **Use the selected customer-value approach for ranking only.** Complete held-out value MAE is GBP 644.46 for BG/NBD + Gamma-Gamma versus GBP 633.45 for the historical-value baseline; **Baseline** is selected.
5. **Adopt the validated TF-IDF product taxonomy** (held-out macro-F1 0.873). The former LLM score was withdrawn because its replay labels were not independent of the gold set.

## What we do NOT know

- **No cost data → no margin.** Every margin figure elsewhere is a labelled scenario.
- **No causality.** Price and retention findings are *associations*; the proposed experiment is required before claiming any uplift.
- **Data age & scope.** 2009–2011, one UK retailer — illustrates method, not current market facts. ~20% of revenue has no customer id.

## Next steps

The SKU-randomised price-floor design is **not powered for its 5% target**: it requires **21,102 SKUs per arm**, versus **1,713 available** over 8 weeks. Even with the historical pre-period adjustment, the available catalogue detects about **17.6%**. Use a smaller pilot only for operational validation, not an uplift claim.
