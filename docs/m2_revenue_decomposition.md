# M2 — Revenue decomposition (findings)

_Generated 2026-11-16 from the DuckDB warehouse. Every figure is computed by `commercial_intelligence.revenue`; do not edit by hand._

## Headline

Comparing **Jan-Nov 2011 vs Jan-Nov 2010**, net product revenue moved from **GBP 8,407,011** to **GBP 8,591,018**, a change of **GBP 184,008 (+2.2%)**.

Three independent lenses each explain this same change exactly. They are shown separately — a product-mix effect and a customer-change effect are two *views* of the one change, never added together.

> **Descriptive, not causal.** These bridges attribute the observed change arithmetically. The price component is *associated* revenue from higher or lower realised prices; it is **not** a price elasticity and says nothing about how volume would respond to a deliberate price change (see M5).

## Comparison periods

The data runs 2009-12-01 to 2011-12-09. December 2009 has no prior-year comparator and December 2011 is a partial month (and carries a large return spike), so the year-on-year bridge uses the **11 complete months January–November** of each year. Partial/edge months are excluded, not pro-rated.

## Lens A — Product price / volume / mix

Price, volume and mix are computed on **gross sales** of products sold in both periods (average realised price = revenue ÷ units). Products new to the current period and products discontinued since the base period are separate bars, and returns (cancellations) are their own bar.

- **Price** = Σ (Pᶜ − Pᵇ)·Qᶜ  · **Volume** = (ΣQᶜ − ΣQᵇ)·P̄ᵇ  · **Mix** = Σ ΔQₚ·Pᵇₚ − Volume

| Component | Value (GBP) | Type |
| --- | ---: | --- |
| Base net revenue | 8,407,010.94 | start |
| Price | -140,936.89 | delta |
| Volume | -1,452,782.23 | delta |
| Mix | 460,178.29 | delta |
| New products | 2,047,430.38 | delta |
| Discontinued products | -664,299.95 | delta |
| Returns (cancellations) | -65,582.08 | delta |
| Unexplained residual | 0.00 | delta |
| Current net revenue | 8,591,018.46 | end |

The unexplained residual is **GBP 0.00** (0.0000% of the change) — rounding dust from the average-price division, included so the waterfall sums exactly.

## Lens B — Customer change

Net revenue split by customer status. Lines without a customer id (about a fifth of revenue) cannot be attributed to a customer and form a separate **guest / unidentified** bar.

| Component | Value (GBP) | Type |
| --- | ---: | --- |
| Base net revenue | 8,407,010.94 | start |
| New customers | 1,378,310.42 | delta |
| Lost customers | -1,055,231.07 | delta |
| Retained customers | -389,162.89 | delta |
| Guest / unidentified | 250,091.06 | delta |
| Residual | 0.00 | delta |
| Current net revenue | 8,591,018.46 | end |

New customers contributed GBP 1,378,310; lost customers removed GBP 1,055,231; retained customers changed by GBP -389,163.

## Lens C — Geography (UK vs International)

| Component | Value (GBP) | Type |
| --- | ---: | --- |
| Base net revenue | 8,407,010.94 | start |
| UK | 2,425.81 | delta |
| International | 182,996.14 | delta |
| Unknown | -1,414.43 | delta |
| Current net revenue | 8,591,018.46 | end |

## Limitations

- The decomposition is **descriptive**: it explains what moved, not why. No causal or elasticity claim is made.
- Average realised price blends list price, quantity-break pricing and customer mix within a product; the price bar therefore mixes true price changes with within-product buyer mix. M5 examines price dispersion.
- Guest revenue (~20%) limits how much of the change the customer lens can attribute to identified behaviour.
- Figures are historical (2010–2011, one UK retailer) and illustrate method.
