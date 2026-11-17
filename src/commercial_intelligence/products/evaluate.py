"""Evaluation metrics for product classification: accuracy, macro-F1, confusion."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

from commercial_intelligence.products.taxonomy import family_codes


def scores(y_true: list[str], y_pred: list[str]) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "n": len(y_true),
    }


def per_class(y_true: list[str], y_pred: list[str]) -> pd.DataFrame:
    labels = [c for c in family_codes() if c in set(y_true) | set(y_pred)]
    p, r, f, s = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    return pd.DataFrame(
        {"family_code": labels, "precision": p, "recall": r, "f1": f, "support": s}
    ).sort_values("support", ascending=False)


def confusion(y_true: list[str], y_pred: list[str]) -> pd.DataFrame:
    labels = [c for c in family_codes() if c in set(y_true) | set(y_pred)]
    m = confusion_matrix(y_true, y_pred, labels=labels)
    return pd.DataFrame(m, index=labels, columns=labels)


def error_table(df: pd.DataFrame, true_col: str, pred_col: str) -> pd.DataFrame:
    """Rows where prediction != gold, for error analysis."""
    errs = df[df[true_col] != df[pred_col]]
    return errs[["stock_code", "description", true_col, pred_col]].reset_index(drop=True)
