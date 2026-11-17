"""Leakage-free customer-value evaluation and scoring.

Model selection uses complete held-out customer value in GBP. Gamma-Gamma is
fitted and scored only for repeat customers with positive calibration monetary
value; everyone else receives a positive calibration-only population fallback.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from lifetimes import BetaGeoFitter, GammaGammaFitter
    from lifetimes.utils import calibration_and_holdout_data, summary_data_from_transaction_data

MODEL_VALUE = "BG/NBD + Gamma-Gamma"
BASELINE_VALUE = "Baseline (historical avg value)"


def build_transactions(con) -> pd.DataFrame:
    """One row per identified customer per positive sale-day."""
    df = con.execute(
        """
        select customer_key as customer_id, invoice_date as date,
               sum(line_amount) as amount
        from fct_order_lines
        where customer_key <> -1 and line_type = 'sale'
        group by customer_key, invoice_date
        having sum(line_amount) > 0
        """
    ).df()
    df["date"] = pd.to_datetime(df["date"])
    return df


@dataclass(frozen=True)
class HoldoutEvaluation:
    calibration_end: date
    observation_end: date
    duration_holdout_days: float
    n_customers: int
    metrics: pd.DataFrame
    purchase_metrics: pd.DataFrame
    calibration_table: pd.DataFrame
    per_customer: pd.DataFrame
    monetary_mae: dict[str, float]
    n_model_fallback: int


def _baseline_prediction(cal: pd.DataFrame, duration_holdout: float) -> np.ndarray:
    freq = cal["frequency_cal"].to_numpy(dtype=float)
    age = cal["T_cal"].to_numpy(dtype=float)
    rate = np.divide(freq, age, out=np.zeros_like(freq), where=age > 0)
    return rate * duration_holdout


def _calibration_aov_predictions(
    cal: pd.DataFrame, penalizer_coef: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, int]:
    """Return model/baseline AOV predictions using calibration data only."""
    freq = cal["frequency_cal"].to_numpy(dtype=float)
    monetary = cal["monetary_value_cal"].to_numpy(dtype=float)
    eligible = (freq > 0) & np.isfinite(monetary) & (monetary > 0)
    if not eligible.any():
        raise ValueError("Gamma-Gamma requires at least one eligible repeat customer")
    global_aov = float(np.average(monetary[eligible], weights=freq[eligible]))
    if not np.isfinite(global_aov) or global_aov <= 0:
        raise ValueError("Calibration AOV fallback must be finite and positive")

    baseline_aov = np.where(eligible, monetary, global_aov)
    model_aov = np.full(len(cal), global_aov, dtype=float)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ggf = GammaGammaFitter(penalizer_coef=penalizer_coef)
        ggf.fit(cal.loc[eligible, "frequency_cal"], cal.loc[eligible, "monetary_value_cal"])
        predicted = ggf.conditional_expected_average_profit(
            cal.loc[eligible, "frequency_cal"], cal.loc[eligible, "monetary_value_cal"]
        ).to_numpy(dtype=float)
    valid = np.isfinite(predicted) & (predicted > 0)
    positions = np.flatnonzero(eligible)
    model_aov[positions[valid]] = predicted[valid]
    model_aov[positions[~valid]] = baseline_aov[positions[~valid]]
    return model_aov, baseline_aov, eligible, global_aov, int((~valid).sum())


def _metrics(name: str, pred: np.ndarray, actual: np.ndarray) -> dict:
    err = pred - actual
    return {
        "method": name,
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err**2))),
        "predicted_total": float(pred.sum()),
        "actual_total": float(actual.sum()),
    }


def evaluate_holdout(
    transactions: pd.DataFrame,
    calibration_end: date,
    observation_end: date,
    penalizer_coef: float,
) -> HoldoutEvaluation:
    cal = calibration_and_holdout_data(
        transactions,
        customer_id_col="customer_id",
        datetime_col="date",
        calibration_period_end=pd.Timestamp(calibration_end),
        observation_period_end=pd.Timestamp(observation_end),
        freq="D",
        monetary_value_col="amount",
    )
    duration_holdout = float(cal["duration_holdout"].iloc[0])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        bgf = BetaGeoFitter(penalizer_coef=penalizer_coef)
        bgf.fit(cal["frequency_cal"], cal["recency_cal"], cal["T_cal"])
        model_purchases = bgf.predict(
            duration_holdout, cal["frequency_cal"], cal["recency_cal"], cal["T_cal"]
        ).to_numpy(dtype=float)
    baseline_purchases = _baseline_prediction(cal, duration_holdout)
    purchase_invalid = ~np.isfinite(model_purchases) | (model_purchases < 0)
    model_purchases = np.where(purchase_invalid, baseline_purchases, model_purchases)
    actual_purchases = cal["frequency_holdout"].to_numpy(dtype=float)

    model_aov, baseline_aov, eligible, global_aov, aov_invalid = (
        _calibration_aov_predictions(cal, penalizer_coef)
    )
    actual_aov = cal["monetary_value_holdout"].fillna(0).to_numpy(dtype=float)
    actual_value = actual_purchases * actual_aov
    model_value = model_purchases * model_aov
    baseline_value = baseline_purchases * baseline_aov
    arrays = (model_aov, baseline_aov, model_value, baseline_value, actual_value)
    if any((~np.isfinite(a)).any() for a in arrays) or any((a < 0).any() for a in arrays):
        raise ValueError("Customer-value evaluation must be finite and non-negative")

    per_customer = pd.DataFrame(
        {
            "customer_id": cal.index.to_numpy(),
            "frequency_cal": cal["frequency_cal"].to_numpy(),
            "actual_holdout": actual_purchases,
            "pred_bgnbd": model_purchases,
            "pred_baseline": baseline_purchases,
            "eligible_gamma_gamma": eligible,
            "pred_model_aov": model_aov,
            "pred_baseline_aov": baseline_aov,
            "actual_holdout_value": actual_value,
            "pred_model_value": model_value,
            "pred_baseline_value": baseline_value,
        }
    )
    purchase_metrics = pd.DataFrame(
        [
            _metrics("BG/NBD", model_purchases, actual_purchases),
            _metrics("Baseline (historical avg)", baseline_purchases, actual_purchases),
        ]
    )
    value_metrics = pd.DataFrame(
        [
            _metrics(MODEL_VALUE, model_value, actual_value),
            _metrics(BASELINE_VALUE, baseline_value, actual_value),
        ]
    )
    cal_table = (
        per_customer.assign(freq_bucket=np.minimum(per_customer["frequency_cal"], 8))
        .groupby("freq_bucket")
        .agg(
            customers=("customer_id", "count"),
            actual=("actual_holdout", "mean"),
            bgnbd=("pred_bgnbd", "mean"),
            baseline=("pred_baseline", "mean"),
        )
        .reset_index()
    )
    monetary_eval = eligible & (actual_purchases > 0) & (actual_aov > 0)
    monetary_mae = {
        "gamma_gamma_mae": float(
            np.mean(np.abs(model_aov[monetary_eval] - actual_aov[monetary_eval]))
        ),
        "baseline_aov_mae": float(
            np.mean(np.abs(baseline_aov[monetary_eval] - actual_aov[monetary_eval]))
        ),
        "n_customers": int(monetary_eval.sum()),
        "calibration_fallback_aov": global_aov,
    }
    return HoldoutEvaluation(
        calibration_end=calibration_end,
        observation_end=observation_end,
        duration_holdout_days=duration_holdout,
        n_customers=int(len(cal)),
        metrics=value_metrics,
        purchase_metrics=purchase_metrics,
        calibration_table=cal_table,
        per_customer=per_customer,
        monetary_mae=monetary_mae,
        n_model_fallback=int(purchase_invalid.sum()) + aov_invalid,
    )


def value_winner(metrics: pd.DataFrame) -> str:
    return str(metrics.sort_values("mae").iloc[0]["method"])


def split_sensitivity(
    transactions: pd.DataFrame,
    calibration_ends: list[date],
    observation_end: date,
    penalizer_coef: float,
) -> pd.DataFrame:
    rows = []
    for split in calibration_ends:
        ev = evaluate_holdout(transactions, split, observation_end, penalizer_coef)
        m = ev.metrics.set_index("method")["mae"]
        rows.append(
            {
                "calibration_end": split.isoformat(),
                "holdout_days": round(ev.duration_holdout_days),
                "customers": ev.n_customers,
                "model_value_mae": float(m[MODEL_VALUE]),
                "baseline_value_mae": float(m[BASELINE_VALUE]),
                "model_wins": bool(m[MODEL_VALUE] < m[BASELINE_VALUE]),
            }
        )
    return pd.DataFrame(rows)


def full_data_clv(
    transactions: pd.DataFrame,
    penalizer_coef: float,
    horizon_days: int,
    chosen_method: str,
) -> pd.DataFrame:
    """Fit full-history scores using the method selected on held-out GBP value."""
    obs_end = transactions["date"].max()
    summary = summary_data_from_transaction_data(
        transactions,
        customer_id_col="customer_id",
        datetime_col="date",
        monetary_value_col="amount",
        observation_period_end=obs_end,
        freq="D",
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        bgf = BetaGeoFitter(penalizer_coef=penalizer_coef)
        bgf.fit(summary["frequency"], summary["recency"], summary["T"])
        model_purchases = bgf.predict(
            horizon_days, summary["frequency"], summary["recency"], summary["T"]
        ).to_numpy(dtype=float)
        summary["prob_alive"] = bgf.conditional_probability_alive(
            summary["frequency"], summary["recency"], summary["T"]
        )
    freq = summary["frequency"].to_numpy(dtype=float)
    age = summary["T"].to_numpy(dtype=float)
    baseline_purchases = np.divide(freq, age, out=np.zeros_like(freq), where=age > 0) * horizon_days
    invalid_purchases = ~np.isfinite(model_purchases) | (model_purchases < 0)
    model_purchases = np.where(invalid_purchases, baseline_purchases, model_purchases)

    monetary = summary["monetary_value"].to_numpy(dtype=float)
    eligible = (freq > 0) & np.isfinite(monetary) & (monetary > 0)
    global_aov = float(np.average(monetary[eligible], weights=freq[eligible]))
    baseline_aov = np.where(eligible, monetary, global_aov)
    model_aov = np.full(len(summary), global_aov, dtype=float)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ggf = GammaGammaFitter(penalizer_coef=penalizer_coef)
        ggf.fit(summary.loc[eligible, "frequency"], summary.loc[eligible, "monetary_value"])
        gg = ggf.conditional_expected_average_profit(
            summary.loc[eligible, "frequency"], summary.loc[eligible, "monetary_value"]
        ).to_numpy(dtype=float)
    valid_gg = np.isfinite(gg) & (gg > 0)
    positions = np.flatnonzero(eligible)
    model_aov[positions[valid_gg]] = gg[valid_gg]
    model_aov[positions[~valid_gg]] = baseline_aov[positions[~valid_gg]]

    model_value = model_purchases * model_aov
    baseline_value = baseline_purchases * baseline_aov
    if chosen_method == MODEL_VALUE:
        chosen_value = model_value
    elif chosen_method == BASELINE_VALUE:
        chosen_value = baseline_value
    else:
        raise ValueError(f"Unknown chosen CLV method: {chosen_method}")
    if (~np.isfinite(chosen_value)).any() or (chosen_value < 0).any():
        raise ValueError("Full-history customer-value scores must be finite and non-negative")

    summary["predicted_purchases_model"] = model_purchases
    summary["predicted_purchases_baseline"] = baseline_purchases
    summary["predicted_aov_model"] = model_aov
    summary["predicted_aov_baseline"] = baseline_aov
    summary["expected_value_model"] = model_value
    summary["expected_value_baseline"] = baseline_value
    summary["expected_clv_horizon"] = chosen_value
    summary["clv_method"] = chosen_method
    summary["gamma_gamma_eligible"] = eligible
    return summary.reset_index().rename(columns={"index": "customer_id"})
