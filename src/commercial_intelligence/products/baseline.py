"""Baseline product classifier: TF-IDF (word + char n-grams) + logistic regression.

Trained only on the dev split, used to predict the test split and the full
catalogue. Deterministic (fixed seed, no randomness beyond the solver).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline


def build_pipeline(seed: int) -> Pipeline:
    # Word n-grams catch whole tokens ("BAG", "CANDLE"); char n-grams catch
    # sub-word and typo signal ("RETROSPOT", "T-LIGHT"). Both feed one LR.
    features = FeatureUnion(
        [
            ("word", TfidfVectorizer(
                analyzer="word", ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)),
        ]
    )
    clf = LogisticRegression(max_iter=2000, C=10.0, class_weight="balanced", random_state=seed)
    return Pipeline([("features", features), ("clf", clf)])


@dataclass
class BaselineModel:
    pipeline: Pipeline

    def predict(self, descriptions: list[str]) -> list[str]:
        return list(self.pipeline.predict(descriptions))


def train_baseline(gold: pd.DataFrame, seed: int) -> BaselineModel:
    dev = gold[gold["split"] == "dev"]
    pipe = build_pipeline(seed)
    pipe.fit(dev["description"].tolist(), dev["family_code"].tolist())
    return BaselineModel(pipe)
