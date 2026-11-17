"""M3: RFM scoring, k-means determinism and cohort-retention invariants on the fixture."""

from __future__ import annotations

import numpy as np

from commercial_intelligence.customers import cohorts, segmentation

VALID_SEGMENTS = {
    "Champions",
    "Loyal customers",
    "Potential loyalist",
    "New customers",
    "Promising / need attention",
    "At risk",
    "Hibernating",
    "Can't lose them",
    "Lost / inactive",
}


def test_rfm_scores_in_range_and_labelled(con):
    rfm = segmentation.add_rfm_scores(segmentation.rfm_table(con))
    assert len(rfm) > 0
    for col in ("r_score", "f_score", "m_score"):
        assert rfm[col].between(1, 5).all()
    assert set(rfm["rfm_segment"]).issubset(VALID_SEGMENTS)
    # Guests must never be segmented.
    assert (rfm["customer_key"] != -1).all()


def test_recency_score_rewards_recent_buyers(con):
    rfm = segmentation.add_rfm_scores(segmentation.rfm_table(con))
    # Higher r_score should correspond to lower (better) recency on average.
    med_hi = rfm.loc[rfm["r_score"] == 5, "recency_days"].median()
    med_lo = rfm.loc[rfm["r_score"] == 1, "recency_days"].median()
    assert med_hi < med_lo


def test_kmeans_is_deterministic(con):
    rfm = segmentation.add_rfm_scores(segmentation.rfm_table(con))
    a = segmentation.kmeans_segments(rfm, [4], seed=42)
    b = segmentation.kmeans_segments(rfm, [4], seed=42)
    assert np.array_equal(a.labels, b.labels)
    assert -1.0 <= a.silhouette <= 1.0
    assert a.k == 4


def test_cohort_offset_zero_is_full_retention(con):
    counts, rates = cohorts.retention_matrix(con)
    # Everyone is active in their own acquisition month.
    assert np.allclose(rates[0].to_numpy(), 1.0)


def test_retention_rates_bounded(con):
    _, rates = cohorts.retention_matrix(con)
    offs = [c for c in rates.columns if isinstance(c, int)]
    vals = rates[offs].to_numpy()
    vals = vals[~np.isnan(vals)]
    assert (vals >= 0).all() and (vals <= 1.0 + 1e-9).all()


def test_retention_curve_decreases_after_acquisition(con):
    _, rates = cohorts.retention_matrix(con)
    curve = cohorts.retention_curve(rates)
    first = curve.loc[curve["month_offset"] == 0, "avg_retention"].iloc[0]
    second = curve.loc[curve["month_offset"] == 1, "avg_retention"].iloc[0]
    assert first == 1.0
    assert second < first
