"""M4 tests for the independently evaluated TF-IDF classifier."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from commercial_intelligence.common.config import load_settings
from commercial_intelligence.products import baseline as base_mod
from commercial_intelligence.products import evaluate
from commercial_intelligence.products.llm_client import from_settings
from commercial_intelligence.products.taxonomy import (
    ProductFamily,
    family_codes,
    load_gold,
)

# ---- gold + taxonomy -------------------------------------------------------

def test_gold_is_well_formed():
    gold = load_gold()
    assert len(gold) == 300
    assert set(gold["family_code"]).issubset(set(family_codes()))
    assert set(gold["split"]) == {"dev", "test"}


def test_every_family_in_both_splits():
    gold = load_gold()
    for split in ("dev", "test"):
        present = set(gold[gold["split"] == split]["family_code"])
        # Every family that exists appears in each split (stratified).
        assert present == set(gold["family_code"])


def test_productfamily_coerces_unknown_code():
    assert ProductFamily(stock_code="X", family_code="NONSENSE").family_code == "OT"
    assert ProductFamily(stock_code="X", family_code="KD").family_code == "KD"


def test_productfamily_confidence_bounds():
    with pytest.raises(ValidationError):
        ProductFamily(stock_code="X", family_code="KD", confidence=1.5)


# ---- baseline --------------------------------------------------------------

def test_baseline_trains_and_predicts_valid_labels():
    gold = load_gold()
    model = base_mod.train_baseline(gold, seed=42)
    test = gold[gold["split"] == "test"]
    preds = model.predict(test["description"].tolist())
    assert len(preds) == len(test)
    assert set(preds).issubset(set(family_codes()))


def test_baseline_is_deterministic():
    gold = load_gold()
    a = base_mod.train_baseline(gold, 42).predict(["RED RETROSPOT MUG", "JUMBO BAG OWLS"])
    b = base_mod.train_baseline(gold, 42).predict(["RED RETROSPOT MUG", "JUMBO BAG OWLS"])
    assert a == b


def test_baseline_training_never_uses_test_labels():
    gold = load_gold()
    test = gold[gold["split"] == "test"]
    original = base_mod.train_baseline(gold, 42).predict(test["description"].tolist())
    changed = gold.copy()
    changed.loc[changed["split"] == "test", "family_code"] = "OT"
    mutated = base_mod.train_baseline(changed, 42).predict(test["description"].tolist())
    assert mutated == original


def test_label_derived_llm_replay_is_fail_closed():
    settings = load_settings()
    assert settings["products"]["llm"]["mode"] == "disabled"
    with pytest.raises(ValueError, match="unknown mode 'disabled'"):
        from_settings(settings)


# ---- metrics ---------------------------------------------------------------

def test_scores_on_perfect_and_imperfect():
    y = ["KD", "BG", "HD", "KD"]
    assert evaluate.scores(y, y)["accuracy"] == 1.0
    assert evaluate.scores(y, y)["macro_f1"] == 1.0
    s = evaluate.scores(y, ["KD", "BG", "KD", "KD"])
    assert 0 < s["accuracy"] < 1


def test_confusion_is_square_over_present_labels():
    y = ["KD", "BG", "HD"]
    p = ["KD", "KD", "HD"]
    cm = evaluate.confusion(y, p)
    assert cm.shape[0] == cm.shape[1]
    assert cm.to_numpy().sum() == len(y)
