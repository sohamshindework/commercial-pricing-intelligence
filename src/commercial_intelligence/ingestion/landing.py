"""Convert the source Excel workbook into one landing Parquet file.

The landing file keeps every source row and every source value. It only adds
lineage columns (`source_sheet`, `source_row`) and stores the two mixed-type
code columns (Invoice, StockCode) as text, because Excel stores e.g. 489434 as
a number and C489449 as text in the same column. All cleaning happens in SQL.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from commercial_intelligence.common.log_utils import get_logger, kv

log = get_logger(__name__)

SOURCE_COLUMNS = [
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country",
]
LANDING_COLUMNS = ["source_sheet", "source_row", *SOURCE_COLUMNS]


def _to_text(value: object) -> str | None:
    """Excel numbers like 85123.0 become '85123'; text is kept as-is; blanks become None."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def sheet_to_landing(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    missing = [c for c in SOURCE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Sheet {sheet_name!r} is missing columns: {missing}")
    out = df[SOURCE_COLUMNS].copy()
    for col in ("Invoice", "StockCode", "Description", "Country"):
        out[col] = out[col].map(_to_text).astype("string")
    out["Quantity"] = out["Quantity"].astype("int64")
    out["Price"] = out["Price"].astype("float64")
    out["Customer ID"] = out["Customer ID"].astype("float64")
    out["InvoiceDate"] = pd.to_datetime(out["InvoiceDate"])
    out.insert(0, "source_sheet", sheet_name)
    # Excel row number: header is row 1, so the first data row is row 2.
    out.insert(1, "source_row", range(2, len(out) + 2))
    out["source_row"] = out["source_row"].astype("int64")
    return out


def excel_to_landing(xlsx_path: Path, parquet_path: Path) -> pd.DataFrame:
    log.info(kv("landing_read_start", file=xlsx_path.name))
    sheets = pd.read_excel(xlsx_path, sheet_name=None, engine="openpyxl")
    frames = [sheet_to_landing(df, name) for name, df in sheets.items()]
    landing = pd.concat(frames, ignore_index=True)[LANDING_COLUMNS]
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    landing.to_parquet(parquet_path, index=False)
    log.info(
        kv("landing_written", file=parquet_path.name, rows=len(landing), sheets=len(frames))
    )
    return landing
