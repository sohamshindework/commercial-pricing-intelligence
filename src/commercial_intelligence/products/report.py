"""Run M4 with the independently evaluated TF-IDF baseline.

The former replay cassette is excluded because it was derived from the gold
labels and cannot support an independent LLM comparison. A future LLM result may
be added only from independently recorded predictions with auditable provenance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd

from commercial_intelligence.common.config import load_settings
from commercial_intelligence.common.log_utils import get_logger, kv
from commercial_intelligence.products import baseline as base_mod
from commercial_intelligence.products import classify, evaluate
from commercial_intelligence.products.taxonomy import code_to_name, load_gold

log = get_logger(__name__)


@dataclass
class M4Outputs:
    gold: pd.DataFrame
    test_scored: pd.DataFrame
    baseline_scores: dict
    per_class_baseline: pd.DataFrame
    confusion_baseline: pd.DataFrame
    errors_baseline: pd.DataFrame
    chosen: str
    catalogue: pd.DataFrame


def run(con: duckdb.DuckDBPyConnection) -> M4Outputs:
    settings = load_settings()
    seed = int(settings["products"]["random_seed"])
    gold = load_gold()
    test = gold[gold["split"] == "test"].reset_index(drop=True)

    baseline = base_mod.train_baseline(gold, seed)
    scored = test.copy()
    scored["baseline_code"] = baseline.predict(test["description"].tolist())
    y = scored["family_code"].tolist()
    scores = evaluate.scores(y, scored["baseline_code"].tolist())
    catalogue = classify.label_catalogue(classify.full_catalogue(con), baseline)
    log.info(
        kv(
            "m4_done",
            baseline_f1=round(scores["macro_f1"], 3),
            chosen="baseline",
            llm_evaluation="withdrawn_label_leakage",
        )
    )
    return M4Outputs(
        gold=gold,
        test_scored=scored,
        baseline_scores=scores,
        per_class_baseline=evaluate.per_class(y, scored["baseline_code"].tolist()),
        confusion_baseline=evaluate.confusion(y, scored["baseline_code"].tolist()),
        errors_baseline=evaluate.error_table(scored, "family_code", "baseline_code"),
        chosen="baseline",
        catalogue=catalogue,
    )


def write_exports(out: M4Outputs, export_dir: Path) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    # Remove withdrawn label-derived LLM artifacts from earlier pipeline runs so
    # no consumer can mistake them for current, admissible evaluation outputs.
    for stem in ("per_class_llm", "confusion_llm", "errors_llm"):
        for suffix in (".csv", ".parquet"):
            (export_dir / f"{stem}{suffix}").unlink(missing_ok=True)
    tables = {
        "test_predictions": out.test_scored,
        "metrics_summary": pd.DataFrame(
            [{"method": "Baseline (TF-IDF + LogReg)", **out.baseline_scores}]
        ),
        "per_class_baseline": out.per_class_baseline,
        "confusion_baseline": out.confusion_baseline.reset_index(names="true_code"),
        "errors_baseline": out.errors_baseline,
        "product_families": out.catalogue,
    }
    for name, df in tables.items():
        df.to_parquet(export_dir / f"{name}.parquet", index=False)
        df.to_csv(export_dir / f"{name}.csv", index=False)
    log.info(kv("m4_exports_written", dir=str(export_dir), tables=len(tables)))


def _md(df: pd.DataFrame, floatfmt: str = "{:.3f}") -> str:
    cols = list(df.columns)
    is_float = {c: pd.api.types.is_float_dtype(df[c]) for c in cols}
    lines = [
        "| " + " | ".join(str(c) for c in cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for row in df.itertuples(index=False, name=None):
        lines.append(
            "| "
            + " | ".join(
                floatfmt.format(v) if is_float[c] else str(v)
                for c, v in zip(cols, row, strict=True)
            )
            + " |"
        )
    return "\n".join(lines)


def render_report(out: M4Outputs) -> str:
    names = code_to_name()
    scores = out.baseline_scores
    distribution = (
        out.catalogue["family_code"]
        .map(names)
        .value_counts()
        .rename_axis("family")
        .reset_index(name="products")
    )
    lines = [
        "# M4 — Product-family classification (corrected findings)",
        "",
        f"_Generated {date.today().isoformat()}. Metrics are computed on the held-out "
        "test split only._",
        "",
        "## Integrity decision",
        "",
        "The previous LLM score has been withdrawn. Its replay cassette was derived from "
        "the gold labels and was not an independent inference run. It is excluded from "
        "evaluation, model selection and catalogue labelling.",
        "",
        "The selected classifier is the reproducible TF-IDF (word and character n-grams) "
        "+ logistic-regression baseline, trained only on the development split. It requires "
        "no API key or paid service.",
        "",
        "## Held-out test result",
        "",
        _md(
            pd.DataFrame(
                [{"method": "Baseline (TF-IDF + LogReg)", **scores}]
            )[["method", "accuracy", "macro_f1", "weighted_f1", "n"]]
        ),
        "",
        "## Per-class quality",
        "",
        _md(
            out.per_class_baseline.assign(
                family=out.per_class_baseline["family_code"].map(names)
            )[["family_code", "family", "precision", "recall", "f1", "support"]],
            "{:.2f}",
        ),
        "",
        "## Full catalogue",
        "",
        f"The baseline labels all **{len(out.catalogue):,} products**; every row records "
        "`family_source=baseline`.",
        "",
        _md(distribution),
        "",
        "## Limitations",
        "",
        "- Gold labels cover 300 best-selling products; long-tail accuracy is not "
        "directly validated.",
        "- Some families have low held-out support, so their per-class metrics are uncertain.",
        "- No independent LLM comparison is currently available. A future comparison must use "
        "predictions recorded without access to test labels and preserve auditable provenance.",
        "",
    ]
    return "\n".join(lines)
