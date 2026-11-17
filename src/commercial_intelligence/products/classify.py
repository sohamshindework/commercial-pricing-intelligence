"""Apply the validated baseline classifier to the full product catalogue."""

from __future__ import annotations

import duckdb
import pandas as pd

from commercial_intelligence.products.baseline import BaselineModel


def full_catalogue(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Every product with a usable description (stock_code, description)."""
    return con.execute(
        """
        select product_key as stock_code, product_name as description
        from dim_product
        where product_name is not null and product_name not ilike 'UNKNOWN%'
        order by product_key
        """
    ).df()


def label_catalogue(
    catalogue: pd.DataFrame,
    baseline: BaselineModel,
) -> pd.DataFrame:
    """Label the whole catalogue with the independently evaluated baseline.

    The former cached-LLM selection branch was removed because its predictions
    were derived from the evaluation labels and therefore cannot be scored or
    selected as an independent model.
    """
    out = catalogue.copy()
    out["family_code"] = baseline.predict(out["description"].tolist())
    out["family_source"] = "baseline"
    return out
