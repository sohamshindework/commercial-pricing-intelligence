"""Pure revenue-decomposition arithmetic (no I/O, no DuckDB).

Three *independent* lenses on the same revenue change, each an exact additive
partition. They are reported side by side, never merged into one bridge, so a
product-mix effect and a customer-change effect are never double-counted.

LENS A - Product price/volume/mix (operates on GROSS sales only)
    Gross sales have quantity > 0 and price > 0 (guaranteed by cleaning rules
    R05/R07), so average realised price = revenue / units is always defined.
    For products sold in BOTH periods ("continuing"):
        price  = Σ (P_c - P_b) · Q_c              (ΔP priced at current volume)
        volume = (ΣQ_c - ΣQ_b) · P̄_b             (total unit change at base avg price)
        mix    = Σ ΔQ_p · P_b,p  −  volume        (shift between products of
                                                    different base prices)
      where P̄_b = ΣRev_b / ΣQ_b over continuing products.
      Identity (per product): (P_c-P_b)Q_c + (Q_c-Q_b)P_b = Rev_c - Rev_b, so
      price + volume + mix = Σ(Rev_c - Rev_b) over continuing products.
    Products only in the current period add `new_products` (their gross revenue);
    products only in the base period subtract `discontinued_products`.
    Cancellations (returns) are handled by the caller as a separate component,
    because they are not part of gross sales.

LENS B - Customer change (operates on NET revenue per customer)
    new / lost / retained customers, plus a `guest` bucket for lines without a
    customer id. No price maths, so this lens is exact to the penny.

LENS C - Geography (operates on NET revenue per market)
    A plain partition of the net change by market (UK / International / Unknown).

Floating-point note: LENS A divides to get average prices, so its parts can
differ from the gross change by rounding dust. The caller closes the bridge with
an explicit `unexplained_residual` so the waterfall still sums exactly; the
residual is reported and asserted to be negligible.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

# entity_key -> (units, revenue). Units and revenue are floats (GBP).
PeriodAgg = Mapping[object, tuple[float, float]]


@dataclass(frozen=True)
class PVMBridge:
    """Product price/volume/mix bridge on gross sales."""

    base_gross: float
    current_gross: float
    price: float
    volume: float
    mix: float
    new_products: float
    discontinued_products: float
    n_continuing: int
    n_new: int
    n_discontinued: int

    @property
    def total_change(self) -> float:
        return self.current_gross - self.base_gross

    @property
    def explained(self) -> float:
        return (
            self.price
            + self.volume
            + self.mix
            + self.new_products
            - self.discontinued_products
        )

    @property
    def residual(self) -> float:
        """Gross change not captured by the parts (float dust; ~0)."""
        return self.total_change - self.explained


def pvm_bridge(base: PeriodAgg, current: PeriodAgg) -> PVMBridge:
    """Price/volume/mix bridge between two periods of per-product gross aggregates.

    base/current map product_key -> (units, revenue), units > 0 for gross sales.
    """
    base = {k: v for k, v in base.items() if v[0] > 0}
    current = {k: v for k, v in current.items() if v[0] > 0}

    continuing = base.keys() & current.keys()
    new_keys = current.keys() - base.keys()
    disc_keys = base.keys() - current.keys()

    price = 0.0
    qty_at_base_price = 0.0
    sum_qb = sum_qc = sum_rev_b = 0.0
    for k in continuing:
        qb, rb = base[k]
        qc, rc = current[k]
        pb, pc = rb / qb, rc / qc
        price += (pc - pb) * qc
        qty_at_base_price += (qc - qb) * pb
        sum_qb += qb
        sum_qc += qc
        sum_rev_b += rb

    avg_base_price = sum_rev_b / sum_qb if sum_qb else 0.0
    volume = (sum_qc - sum_qb) * avg_base_price
    mix = qty_at_base_price - volume

    new_products = sum(rev for _, rev in (current[k] for k in new_keys))
    discontinued_products = sum(rev for _, rev in (base[k] for k in disc_keys))

    return PVMBridge(
        base_gross=sum(rev for _, rev in base.values()),
        current_gross=sum(rev for _, rev in current.values()),
        price=price,
        volume=volume,
        mix=mix,
        new_products=new_products,
        discontinued_products=discontinued_products,
        n_continuing=len(continuing),
        n_new=len(new_keys),
        n_discontinued=len(disc_keys),
    )


@dataclass(frozen=True)
class CustomerBridge:
    """Net-revenue change split by customer status."""

    base_net: float
    current_net: float
    new_customers: float
    lost_customers: float
    retained_customers: float
    guest: float
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def total_change(self) -> float:
        return self.current_net - self.base_net

    @property
    def explained(self) -> float:
        return (
            self.new_customers
            - self.lost_customers
            + self.retained_customers
            + self.guest
        )

    @property
    def residual(self) -> float:
        return self.total_change - self.explained


def customer_bridge(
    base: Mapping[object, float],
    current: Mapping[object, float],
    guest_key: object = -1,
) -> CustomerBridge:
    """Net-revenue bridge by customer status.

    base/current map customer_key -> net revenue (guest_key = unidentified).
    """
    base_ids = {k for k in base if k != guest_key}
    cur_ids = {k for k in current if k != guest_key}

    retained_ids = base_ids & cur_ids
    new_ids = cur_ids - base_ids
    lost_ids = base_ids - cur_ids

    new_customers = sum(current[k] for k in new_ids)
    lost_customers = sum(base[k] for k in lost_ids)
    retained = sum(current[k] - base[k] for k in retained_ids)
    guest = current.get(guest_key, 0.0) - base.get(guest_key, 0.0)

    return CustomerBridge(
        base_net=sum(base.values()),
        current_net=sum(current.values()),
        new_customers=new_customers,
        lost_customers=lost_customers,
        retained_customers=retained,
        guest=guest,
        counts={
            "retained": len(retained_ids),
            "new": len(new_ids),
            "lost": len(lost_ids),
        },
    )


def geography_bridge(
    base: Mapping[object, float], current: Mapping[object, float]
) -> dict[object, float]:
    """Net-revenue change per market key. Exact partition; values sum to ΔNet."""
    markets = base.keys() | current.keys()
    return {m: current.get(m, 0.0) - base.get(m, 0.0) for m in markets}
