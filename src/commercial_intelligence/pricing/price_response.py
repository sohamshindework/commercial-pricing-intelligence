"""Descriptive log-log price-quantity association by product family.

STRICTLY NON-CAUSAL. For each family we regress log(quantity) on log(unit_price)
over sale lines, two ways:

  * **pooled:** log(q) ~ log(p). Mixes across products, so it mostly reflects that
    cheap products sell in larger quantities — not a price response.
  * **within-product:** the same regression after subtracting each product's own
    means from log(q) and log(p) (a product fixed-effect / within estimator), so
    it uses only price variation *for the same product over time*.

The within-product slope is the more comparable figure, but it is still an
*association*, confounded by quantity-break pricing, seasonality and customer mix.
It is NOT a price elasticity and must never be used to predict the revenue effect
of a deliberate price change. Reported with HC1 robust 95% confidence intervals.
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm


@dataclass
class FamilySlope:
    family_code: str
    n_lines: int
    n_products: int
    pooled_slope: float
    pooled_ci_low: float
    pooled_ci_high: float
    within_slope: float
    within_ci_low: float
    within_ci_high: float


def _ols_slope(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    X = sm.add_constant(x)
    model = sm.OLS(y, X).fit(cov_type="HC1")
    coef = model.params[1]
    lo, hi = model.conf_int()[1]
    return float(coef), float(lo), float(hi)


def load_sale_lines_with_family(
    con: duckdb.DuckDBPyConnection, families: pd.DataFrame
) -> pd.DataFrame:
    lines = con.execute(
        """
        select product_key, quantity, unit_price
        from fct_order_lines
        where line_type = 'sale' and quantity > 0 and unit_price > 0 and not is_extreme_line
        """
    ).df()
    fam = families[["stock_code", "family_code"]].rename(columns={"stock_code": "product_key"})
    merged = lines.merge(fam, on="product_key", how="inner")
    merged["log_q"] = np.log(merged["quantity"].astype(float))
    merged["log_p"] = np.log(merged["unit_price"].astype(float))
    return merged


def family_slopes(df: pd.DataFrame, min_lines: int = 200) -> list[FamilySlope]:
    out: list[FamilySlope] = []
    for code, g in df.groupby("family_code"):
        if len(g) < min_lines or g["product_key"].nunique() < 5:
            continue
        ps, plo, phi = _ols_slope(g["log_p"].to_numpy(), g["log_q"].to_numpy())

        # within-product: subtract each product's mean from log_q and log_p
        gm = g.copy()
        gm["log_q_d"] = gm["log_q"] - gm.groupby("product_key")["log_q"].transform("mean")
        gm["log_p_d"] = gm["log_p"] - gm.groupby("product_key")["log_p"].transform("mean")
        varying = gm[gm["log_p_d"].abs() > 1e-9]
        if len(varying) < min_lines:
            continue
        ws, wlo, whi = _ols_slope(varying["log_p_d"].to_numpy(), varying["log_q_d"].to_numpy())

        out.append(
            FamilySlope(
                family_code=code,
                n_lines=int(len(g)),
                n_products=int(g["product_key"].nunique()),
                pooled_slope=ps, pooled_ci_low=plo, pooled_ci_high=phi,
                within_slope=ws, within_ci_low=wlo, within_ci_high=whi,
            )
        )
    return out


def slopes_frame(slopes: list[FamilySlope]) -> pd.DataFrame:
    return pd.DataFrame([s.__dict__ for s in slopes]).sort_values("within_slope")
