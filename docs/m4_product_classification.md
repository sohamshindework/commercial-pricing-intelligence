# M4 — Product-family classification (corrected findings)

_Generated 2026-11-16. Metrics are computed on the held-out test split only._

## Integrity decision

The previous LLM score has been withdrawn. Its replay cassette was derived from the gold labels and was not an independent inference run. It is excluded from evaluation, model selection and catalogue labelling.

The selected classifier is the reproducible TF-IDF (word and character n-grams) + logistic-regression baseline, trained only on the development split. It requires no API key or paid service.

## Held-out test result

| method | accuracy | macro_f1 | weighted_f1 | n |
| --- | --- | --- | --- | --- |
| Baseline (TF-IDF + LogReg) | 0.891 | 0.873 | 0.887 | 147 |

## Per-class quality

| family_code | family | precision | recall | f1 | support |
| --- | --- | --- | --- | --- | --- |
| KD | Kitchen & Dining | 0.85 | 0.94 | 0.89 | 35 |
| HD | Home Decor & Ornaments | 0.82 | 0.96 | 0.88 | 24 |
| BG | Bags & Luggage | 1.00 | 1.00 | 1.00 | 21 |
| SP | Signs & Plaques | 0.79 | 0.92 | 0.85 | 12 |
| PC | Party & Celebration | 1.00 | 0.73 | 0.84 | 11 |
| TX | Textiles & Soft Furnishings | 1.00 | 1.00 | 1.00 | 10 |
| SC | Stationery & Craft | 0.78 | 0.78 | 0.78 | 9 |
| TG | Toys & Games | 1.00 | 0.62 | 0.77 | 8 |
| CL | Candles & Lighting | 1.00 | 0.71 | 0.83 | 7 |
| XM | Christmas & Seasonal | 1.00 | 1.00 | 1.00 | 3 |
| FA | Fashion & Accessories | 1.00 | 0.33 | 0.50 | 3 |
| OT | Other / Unsure | 1.00 | 1.00 | 1.00 | 3 |
| GO | Garden & Outdoor | 1.00 | 1.00 | 1.00 | 1 |

## Full catalogue

The baseline labels all **4,739 products**; every row records `family_source=baseline`.

| family | products |
| --- | --- |
| Home Decor & Ornaments | 1490 |
| Kitchen & Dining | 1435 |
| Stationery & Craft | 257 |
| Bags & Luggage | 257 |
| Candles & Lighting | 247 |
| Party & Celebration | 198 |
| Toys & Games | 184 |
| Christmas & Seasonal | 179 |
| Signs & Plaques | 173 |
| Textiles & Soft Furnishings | 143 |
| Fashion & Accessories | 100 |
| Garden & Outdoor | 53 |
| Other / Unsure | 23 |

## Limitations

- Gold labels cover 300 best-selling products; long-tail accuracy is not directly validated.
- Some families have low held-out support, so their per-class metrics are uncertain.
- No independent LLM comparison is currently available. A future comparison must use predictions recorded without access to test labels and preserve auditable provenance.
