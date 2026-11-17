"""M5 acceptance: the power calculation agrees with statsmodels."""

from __future__ import annotations

import math

import pytest
from statsmodels.stats.power import TTestIndPower

from commercial_intelligence.pricing.experiment import (
    design_price_experiment,
    effect_size,
    minimum_detectable_effect,
    sample_size_normal_approx,
    sample_size_statsmodels,
)


@pytest.mark.parametrize(
    "mean,sd,mde",
    [(100.0, 80.0, 0.20), (50.0, 40.0, 0.15), (200.0, 150.0, 0.10), (10.0, 6.0, 0.25)],
)
def test_normal_approx_matches_statsmodels(mean, sd, mde):
    approx = sample_size_normal_approx(mean, sd, mde)
    sm = sample_size_statsmodels(mean, sd, mde).n_per_group
    # The closed-form z-approx and statsmodels' t-based solver agree within 5%.
    assert abs(approx - sm) / sm < 0.05


def test_statsmodels_result_satisfies_target_power():
    res = sample_size_statsmodels(100.0, 80.0, 0.20, alpha=0.05, power=0.80)
    achieved = TTestIndPower().power(
        effect_size=res.effect_size_d, nobs1=res.n_per_group, alpha=0.05, ratio=1.0
    )
    assert achieved >= 0.80


def test_effect_size_formula():
    assert effect_size(100.0, 50.0, 0.10) == pytest.approx(0.2)
    with pytest.raises(ValueError):
        effect_size(100.0, 0.0, 0.1)


def test_mde_round_trips():
    res = sample_size_statsmodels(100.0, 80.0, 0.20)
    mde = minimum_detectable_effect(100.0, 80.0, res.n_per_group)
    assert mde == pytest.approx(0.20, abs=0.005)


def test_smaller_mde_needs_larger_sample():
    big_mde = sample_size_statsmodels(100.0, 80.0, 0.30).n_per_group
    small_mde = sample_size_statsmodels(100.0, 80.0, 0.10).n_per_group
    assert small_mde > big_mde
    assert math.isfinite(small_mde)


def test_sku_randomisation_does_not_treat_weeks_as_independent_units():
    power = sample_size_statsmodels(50.0, 95.0, 0.05)
    design = design_price_experiment(
        power,
        eligible_products=3401,
        weeks_available=8,
        mde_available_unadjusted=0.28,
        mde_available_adjusted=0.18,
        preperiod_correlation=0.75,
    )
    assert design.required_products_per_arm == power.n_per_group
    assert design.available_products_per_arm == 1700
    assert design.required_products_per_arm != math.ceil(power.n_per_group / 8)
    assert not design.adequately_powered
