"""Small, dataset-free unit tests for the landing conversion helpers."""

from __future__ import annotations

import pandas as pd

from commercial_intelligence.ingestion.landing import _to_text, sheet_to_landing


def test_to_text_numeric_codes_lose_trailing_zero():
    assert _to_text(85123.0) == "85123"
    assert _to_text("C489449") == "C489449"
    assert _to_text(None) is None
    assert _to_text(float("nan")) is None


def test_sheet_to_landing_adds_lineage_and_types():
    df = pd.DataFrame(
        {
            "Invoice": [489434, "C489449"],
            "StockCode": [85048, "85123A"],
            "Description": ["  WIDGET   BLUE ", None],
            "Quantity": [6, -1],
            "InvoiceDate": ["2009-12-01 07:45:00", "2009-12-01 10:00:00"],
            "Price": [1.25, 2.0],
            "Customer ID": [13085.0, None],
            "Country": ["United Kingdom", "France"],
        }
    )
    out = sheet_to_landing(df, "Year 2009-2010")
    assert list(out["source_row"]) == [2, 3]
    assert out["Invoice"].tolist() == ["489434", "C489449"]
    assert out["StockCode"].tolist() == ["85048", "85123A"]
    assert out["source_sheet"].iloc[0] == "Year 2009-2010"
    assert str(out["InvoiceDate"].dtype).startswith("datetime64")
