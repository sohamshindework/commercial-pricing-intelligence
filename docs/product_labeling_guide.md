# Product-family labelling guide (M4)

## Purpose

The source data has free-text `Description` but no reliable category. To compare
a baseline classifier with an LLM, we need an independent **gold** set of labels.

## Taxonomy

13 families, defined in [`data/labels/taxonomy.csv`](../data/labels/taxonomy.csv),
including an explicit **Other / Unsure** so nothing is forced into a wrong family.
The families: Kitchen & Dining, Home Decor & Ornaments, Candles & Lighting, Bags &
Luggage, Textiles & Soft Furnishings, Stationery & Craft, Toys & Games, Christmas &
Seasonal, Garden & Outdoor, Signs & Plaques, Fashion & Accessories, Party &
Celebration, Other / Unsure.

## Which products

The 300 products with the most **sale lines** (the commercially important,
cleanly-described items), selected deterministically (most lines first, then
stock code). Labelling the best-sellers means the evaluation reflects the
products that actually drive revenue.

## How labels were assigned

The author assigned one family per product by reading the description against the
taxonomy definitions. Labels are the author's judgement, **independent of the
baseline model and of the LLM classifier**. Consistent tie-break rules were used
for recurring edge cases:

- **Cake cases** → Kitchen & Dining (baking); **paper napkins / plates / cups /
  doilies** → Party & Celebration (disposable party tableware).
- **Lunch _bag_** → Bags & Luggage; **lunch _box_** → Kitchen & Dining.
- **Kitchen/laundry linens** (oven gloves, tea towels, aprons, washing-up gloves,
  peg bags, clothes pegs) → Kitchen & Dining; **hot water bottles, hand warmers,
  cushions** → Textiles & Soft Furnishings.
- **Doormats, clocks, drawer knobs, hooks, frames, trinket boxes, word blocks** →
  Home Decor & Ornaments.
- **Metal signs, chalkboards, memo boards** → Signs & Plaques.
- Anything explicitly **Christmas / Scandinavian-Christmas** → Christmas & Seasonal,
  regardless of the object.
- **Party/birthday candles** → Party & Celebration; other candles, t-light holders,
  lanterns, night lights, string lights → Candles & Lighting.

## Split

Deterministic, stratified by family: within each family, products are sorted by
stock code and alternated dev/test. Result: 153 dev / 147 test, every family
present in both. The baseline trains on **dev only**; all reported metrics are on
**test only**.

## Known-ambiguous items

Some products genuinely admit more than one family (a child's apron is both
kitchen and clothing; a "toy tidy" is both a bag and a soft-furnishing; novelty
plasters-in-a-tin fit no family well). These are exactly where the LLM's zero-shot
reading diverges from the author's deliberated gold label. The divergences are
listed and annotated in
[`scripts/record_llm_cassette.py`](../scripts/record_llm_cassette.py); they are
real disagreements on hard cases, counted honestly against the LLM in the
evaluation.

## Integrity note

The cached predictions are retained only as test fixtures and are not used for model
selection or catalogue labelling. The independently evaluated TF-IDF baseline is the
production reference.
