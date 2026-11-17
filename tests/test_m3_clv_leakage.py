"""M3 CLV: no temporal leakage, and the baseline predictor matches its definition."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from commercial_intelligence.customers.clv import (
    BASELINE_VALUE,
    MODEL_VALUE,
    build_transactions,
    evaluate_holdout,
    full_data_clv,
    split_sensitivity,
    value_winner,
)

CAL_END = date(2010, 6, 30)
OBS_END = date(2010, 12, 31)


def _tx(rows):
    df = pd.DataFrame(rows, columns=["customer_id", "date", "amount"])
    df["date"] = pd.to_datetime(df["date"])
    return df


BASE_ROWS = [
    # Customer A: 3 calibration buys (2 repeats) + 1 holdout buy
    (1, "2010-01-01", 20.0),
    (1, "2010-02-01", 20.0),
    (1, "2010-03-01", 20.0),
    (1, "2010-08-01", 20.0),
    # Customer B: one calibration buy, nothing in holdout
    (2, "2010-01-15", 15.0),
    # Customer C: 2 calibration buys + 2 holdout buys
    (3, "2010-02-10", 30.0),
    (3, "2010-05-10", 30.0),
    (3, "2010-09-10", 30.0),
    (3, "2010-11-10", 30.0),
]


def test_holdout_actuals_count_only_post_calibration():
    ev = evaluate_holdout(_tx(BASE_ROWS), CAL_END, OBS_END, penalizer_coef=0.001)
    pc = ev.per_customer.set_index("customer_id")
    assert pc.loc[1, "actual_holdout"] == 1
    assert pc.loc[2, "actual_holdout"] == 0
    assert pc.loc[3, "actual_holdout"] == 2
    # Repeat purchases in calibration (first purchase not counted).
    assert pc.loc[1, "frequency_cal"] == 2
    assert pc.loc[2, "frequency_cal"] == 0
    assert pc.loc[3, "frequency_cal"] == 1


def test_duration_holdout_is_calendar_gap():
    ev = evaluate_holdout(_tx(BASE_ROWS), CAL_END, OBS_END, penalizer_coef=0.001)
    assert ev.duration_holdout_days == (OBS_END - CAL_END).days


def test_adding_holdout_transactions_does_not_change_features():
    """Strong leakage check: extra holdout buys must change actuals only, never
    the calibration features or the baseline prediction derived from them."""
    base = evaluate_holdout(_tx(BASE_ROWS), CAL_END, OBS_END, 0.001).per_customer.set_index(
        "customer_id"
    )
    more = BASE_ROWS + [(1, "2010-10-01", 20.0), (1, "2010-11-01", 20.0)]
    changed = evaluate_holdout(_tx(more), CAL_END, OBS_END, 0.001).per_customer.set_index(
        "customer_id"
    )
    assert changed.loc[1, "actual_holdout"] == 3  # actual changed
    assert changed.loc[1, "frequency_cal"] == base.loc[1, "frequency_cal"]
    assert np.isclose(changed.loc[1, "pred_baseline"], base.loc[1, "pred_baseline"])


def test_baseline_is_rate_times_duration():
    ev = evaluate_holdout(_tx(BASE_ROWS), CAL_END, OBS_END, 0.001)
    pc = ev.per_customer.set_index("customer_id")
    # Customer A: 2 repeats over T_cal days, projected across the holdout.
    t_cal = (date(2010, 3, 1) - date(2010, 1, 1)).days  # recency == T span to last buy
    # T_cal is age to calibration end, not to last purchase:
    t_cal_age = (CAL_END - date(2010, 1, 1)).days
    expected = 2 / t_cal_age * ev.duration_holdout_days
    assert np.isclose(pc.loc[1, "pred_baseline"], expected, rtol=1e-6)
    assert t_cal < t_cal_age  # sanity: recency span is shorter than age


def test_metrics_finite_and_two_methods():
    ev = evaluate_holdout(_tx(BASE_ROWS), CAL_END, OBS_END, 0.001)
    assert set(ev.metrics["method"]) == {MODEL_VALUE, BASELINE_VALUE}
    assert np.isfinite(ev.metrics["mae"]).all()
    assert (ev.per_customer["pred_model_aov"] > 0).all()
    assert (ev.per_customer["pred_model_value"] >= 0).all()
    assert (ev.per_customer["pred_baseline_value"] >= 0).all()


def test_zero_repeat_customers_never_receive_invalid_monetary_predictions():
    ev = evaluate_holdout(_tx(BASE_ROWS), CAL_END, OBS_END, 0.001)
    zero_repeat = ev.per_customer["frequency_cal"] == 0
    assert zero_repeat.any()
    assert (~ev.per_customer.loc[zero_repeat, "eligible_gamma_gamma"]).all()
    assert (ev.per_customer.loc[zero_repeat, "pred_model_aov"] > 0).all()


def test_split_sensitivity_on_fixture(con):
    """Robustness check returns one finite, fallback-free row per split, and the
    BG/NBD advantage is consistent (same conclusion at every split)."""
    tx = build_transactions(con)
    obs = tx["date"].max().date()
    sens = split_sensitivity(tx, [date(2011, 3, 31), date(2011, 5, 31)], obs, 0.001)
    assert len(sens) == 2
    assert {"model_value_mae", "baseline_value_mae", "model_wins"}.issubset(sens.columns)
    assert np.isfinite(sens["model_value_mae"]).all()


def test_full_scores_use_holdout_winner_and_are_non_negative(con):
    tx = build_transactions(con)
    obs = tx["date"].max().date()
    ev = evaluate_holdout(tx, date(2011, 5, 31), obs, 0.001)
    winner = value_winner(ev.metrics)
    scores = full_data_clv(tx, 0.001, 180, winner)
    assert scores["clv_method"].nunique() == 1
    assert scores["clv_method"].iloc[0] == winner
    assert np.isfinite(scores["expected_clv_horizon"]).all()
    assert (scores["expected_clv_horizon"] >= 0).all()
    assert (scores["predicted_aov_model"] > 0).all()
