"""RFM segmentation (business-labelled) and k-means on scaled RFM.

Only identified customers with at least one sale are segmented; guests
(customer_key = -1) are excluded. Recency/Frequency/Monetary are measured as of
a reference date (the last transaction date), so the view is a single snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import duckdb
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

RFM_FEATURES = ["recency_days", "frequency", "monetary"]


def reference_date(con: duckdb.DuckDBPyConnection) -> date:
    (d,) = con.execute("select max(invoice_date) from fct_order_lines").fetchone()
    return d


def rfm_table(
    con: duckdb.DuckDBPyConnection,
    as_of: date | None = None,
    start: date | None = None,
) -> pd.DataFrame:
    """One row per identified customer: recency (days), frequency (orders), monetary (net GBP).

    Frequency counts distinct sale invoices; monetary is net revenue (sales minus
    returns) within [start, as_of]. Customers with no sale in the window are excluded.
    """
    as_of = as_of or reference_date(con)
    start = start or date(1900, 1, 1)
    return con.execute(
        """
        with sales as (
            select customer_key, invoice_no, invoice_date, line_amount, line_type
            from fct_order_lines
            where customer_key <> -1 and invoice_date between ? and ?
        )
        select
            customer_key,
            date_diff('day', max(invoice_date) filter (where line_type = 'sale'), ?)
                                                                                    as recency_days,
            count(distinct invoice_no) filter (where line_type = 'sale')             as frequency,
            sum(line_amount)                                                         as monetary,
            min(invoice_date) filter (where line_type = 'sale')                      as first_sale,
            max(invoice_date) filter (where line_type = 'sale')                      as last_sale
        from sales
        group by customer_key
        having count(distinct invoice_no) filter (where line_type = 'sale') >= 1
        order by customer_key
        """,
        [start, as_of, as_of],
    ).df()


def _score_1_to_5(series: pd.Series, ascending: bool) -> pd.Series:
    """Quintile score 1-5 by rank (robust to ties). ascending=True -> high value scores 5."""
    ranks = series.rank(method="first", ascending=ascending)
    # 5 bins on the ranks; label 1..5 so that the best gets 5.
    binned = pd.qcut(ranks, 5, labels=[1, 2, 3, 4, 5])
    return binned.astype(int)


def add_rfm_scores(rfm: pd.DataFrame) -> pd.DataFrame:
    out = rfm.copy()
    out["r_score"] = _score_1_to_5(out["recency_days"], ascending=False)  # recent -> 5
    out["f_score"] = _score_1_to_5(out["frequency"], ascending=True)
    out["m_score"] = _score_1_to_5(out["monetary"].clip(lower=0), ascending=True)
    out["rfm_segment"] = [
        _rfm_label(r, f, m)
        for r, f, m in zip(out["r_score"], out["f_score"], out["m_score"], strict=True)
    ]
    return out


def _rfm_label(r: int, f: int, m: int) -> str:
    """Readable business labels from the classic R x FM grid."""
    fm = round((f + m) / 2)
    if r >= 4 and fm >= 4:
        return "Champions"
    if r >= 3 and fm >= 4:
        return "Loyal customers"
    if r >= 4 and fm >= 2:
        return "Potential loyalist"
    if r >= 4 and fm == 1:
        return "New customers"
    if r == 3 and fm <= 3:
        return "Promising / need attention"
    if r == 2 and fm >= 4:
        return "At risk"
    if r == 2 and fm >= 2:
        return "Hibernating"
    if r == 1 and fm >= 4:
        return "Can't lose them"
    return "Lost / inactive"


@dataclass(frozen=True)
class KMeansResult:
    k: int
    labels: np.ndarray
    silhouette: float
    scores_by_k: dict[int, float]
    model: KMeans
    scaler: StandardScaler


def _features(rfm: pd.DataFrame) -> np.ndarray:
    # Log-compress the heavy right tails of frequency and monetary before scaling.
    f = np.column_stack(
        [
            rfm["recency_days"].to_numpy(dtype=float),
            np.log1p(rfm["frequency"].to_numpy(dtype=float)),
            np.log1p(rfm["monetary"].clip(lower=0).to_numpy(dtype=float)),
        ]
    )
    return f


def kmeans_segments(
    rfm: pd.DataFrame, k_candidates: list[int], seed: int
) -> KMeansResult:
    scaler = StandardScaler().fit(_features(rfm))
    x = scaler.transform(_features(rfm))
    scores: dict[int, float] = {}
    best_k, best_sil, best_model, best_labels = None, -1.0, None, None
    for k in k_candidates:
        model = KMeans(n_clusters=k, random_state=seed, n_init=10)
        labels = model.fit_predict(x)
        sil = float(silhouette_score(x, labels))
        scores[k] = sil
        if sil > best_sil:
            best_k, best_sil, best_model, best_labels = k, sil, model, labels
    return KMeansResult(best_k, best_labels, best_sil, scores, best_model, scaler)


def segment_stability(
    con: duckdb.DuckDBPyConnection, split: date, k: int, seed: int
) -> dict[str, float]:
    """Fit RFM k-means independently on two time windows; compare by Adjusted Rand Index.

    ARI is label-invariant, so no cluster re-alignment is needed. ~1 = stable
    segmentation, ~0 = no better than chance.
    """
    (obs_end,) = con.execute("select max(invoice_date) from fct_order_lines").fetchone()
    early = add_rfm_scores(rfm_table(con, as_of=split))
    late = add_rfm_scores(rfm_table(con, as_of=obs_end, start=split))

    early_lab = kmeans_segments(early, [k], seed)
    late_lab = kmeans_segments(late, [k], seed)
    early = early.assign(cluster=early_lab.labels)
    late = late.assign(cluster=late_lab.labels)

    merged = early.merge(late, on="customer_key", suffixes=("_early", "_late"))
    if len(merged) < k:
        return {"ari": float("nan"), "n_common": len(merged)}
    ari = adjusted_rand_score(merged["cluster_early"], merged["cluster_late"])
    return {"ari": float(ari), "n_common": int(len(merged))}


def describe_clusters(rfm: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    df = rfm.assign(cluster=labels)
    return (
        df.groupby("cluster")
        .agg(
            customers=("customer_key", "count"),
            recency_days=("recency_days", "median"),
            frequency=("frequency", "median"),
            monetary=("monetary", "median"),
            total_monetary=("monetary", "sum"),
        )
        .reset_index()
        .sort_values("total_monetary", ascending=False)
    )
