# data/

Raw and generated data are **not** committed (see `.gitignore`). Only the small
sample fixture lives in `tests/fixtures/`.

| Path | Contents | Created by |
|---|---|---|
| `data/raw/` | downloaded zip + `online_retail_II.xlsx` + landing Parquet | `scripts/download.py` |
| `data/warehouse/commercial.duckdb` | staged, cleaned and star-schema tables | `scripts/build_marts.py` |

## Reproduce

```bash
pip install -e ".[dev]"
python scripts/download.py      # fetch + checksum + write landing Parquet
python scripts/build_marts.py   # build the DuckDB warehouse + data-quality report
```

## Dataset

UCI Online Retail II — real transactions of a UK online gift retailer,
Dec 2009 – Dec 2011. Licence **CC BY 4.0**.
Source: <https://archive.ics.uci.edu/dataset/502/online+retail+ii>.
Chen, D. (2019). *Online Retail II* [Dataset]. UCI Machine Learning Repository.
<https://doi.org/10.24432/C5CG6D>.

The data is historical and from one retailer; figures illustrate the method,
not current market facts. Revenue is in GBP.
