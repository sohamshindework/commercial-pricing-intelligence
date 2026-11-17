"""Hand-computed unit tests for the pure decomposition functions (no dataset)."""

from __future__ import annotations

import math

from commercial_intelligence.revenue.decomposition import (
    customer_bridge,
    geography_bridge,
    pvm_bridge,
)


def _close(a: float, b: float, tol: float = 1e-9) -> bool:
    return math.isclose(a, b, abs_tol=tol)


def test_pvm_price_only():
    # Same units, price 10 -> 11 on one product.
    b = pvm_bridge({"A": (10, 100)}, {"A": (10, 110)})
    assert _close(b.price, 10)
    assert _close(b.volume, 0)
    assert _close(b.mix, 0)
    assert b.new_products == 0 and b.discontinued_products == 0
    assert _close(b.residual, 0)


def test_pvm_volume_only():
    b = pvm_bridge({"A": (10, 100)}, {"A": (20, 200)})
    assert _close(b.price, 0)
    assert _close(b.volume, 100)
    assert _close(b.mix, 0)
    assert _close(b.residual, 0)


def test_pvm_mix_shifts_to_higher_priced_product():
    # Total units unchanged (20 -> 20) but volume moves from the £5 to the £10 line.
    base = {"A": (10, 100), "B": (10, 50)}  # P_A=10, P_B=5
    current = {"A": (15, 150), "B": (5, 25)}
    b = pvm_bridge(base, current)
    assert _close(b.price, 0)
    assert _close(b.volume, 0)  # total units constant
    assert _close(b.mix, 25)  # shift to the dearer product
    assert _close(b.explained, b.total_change)


def test_pvm_new_and_discontinued():
    new = pvm_bridge({"A": (10, 100)}, {"A": (10, 100), "B": (5, 50)})
    assert _close(new.new_products, 50)
    assert new.n_new == 1
    disc = pvm_bridge({"A": (10, 100), "B": (5, 50)}, {"A": (10, 100)})
    assert _close(disc.discontinued_products, 50)
    assert disc.n_discontinued == 1


def test_pvm_ignores_nonpositive_units():
    # A zero/negative-unit entry (e.g. a product that is all returns in the period)
    # is not part of gross sales and must be dropped, not crash the average price.
    b = pvm_bridge({"A": (10, 100)}, {"A": (10, 100), "B": (0, 0), "C": (-3, -9)})
    assert b.n_new == 0
    assert _close(b.total_change, 0)
    assert _close(b.residual, 0)


def test_pvm_full_identity_mixed():
    base = {"A": (100, 1000), "B": (40, 200), "D": (10, 90)}  # D discontinued
    current = {"A": (120, 1320), "B": (30, 180), "N": (5, 75)}  # N new
    b = pvm_bridge(base, current)
    assert _close(b.explained, b.total_change)


def test_customer_bridge_identity():
    base = {1: 100.0, 2: 50.0, -1: 30.0}
    current = {1: 120.0, 3: 40.0, -1: 35.0}
    cb = customer_bridge(base, current)
    assert _close(cb.new_customers, 40)
    assert _close(cb.lost_customers, 50)
    assert _close(cb.retained_customers, 20)
    assert _close(cb.guest, 5)
    assert _close(cb.explained, cb.total_change)
    assert cb.counts == {"retained": 1, "new": 1, "lost": 1}


def test_customer_bridge_guest_only():
    cb = customer_bridge({-1: 100.0}, {-1: 160.0})
    assert _close(cb.guest, 60)
    assert cb.new_customers == 0 and cb.lost_customers == 0
    assert _close(cb.explained, cb.total_change)


def test_geography_bridge_partitions_change():
    changes = geography_bridge(
        {"UK": 100.0, "International": 50.0}, {"UK": 90.0, "International": 80.0}
    )
    assert _close(changes["UK"], -10)
    assert _close(changes["International"], 30)
    assert _close(sum(changes.values()), 20)
