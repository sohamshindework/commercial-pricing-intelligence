"""M3: RFM segmentation is reproducible regardless of warehouse row order."""

from __future__ import annotations

from commercial_intelligence.customers import segmentation


def test_rfm_segments_are_order_independent(con):
    a = segmentation.add_rfm_scores(segmentation.rfm_table(con))
    b = segmentation.add_rfm_scores(segmentation.rfm_table(con))
    a = a.sort_values("customer_key").reset_index(drop=True)
    b = b.sort_values("customer_key").reset_index(drop=True)
    # Same scores and labels every time (deterministic SQL order + rank).
    assert a[["r_score", "f_score", "m_score", "rfm_segment"]].equals(
        b[["r_score", "f_score", "m_score", "rfm_segment"]]
    )
    counts = a["rfm_segment"].value_counts().to_dict()
    assert sum(counts.values()) == len(a)
