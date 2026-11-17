"""Provider-agnostic LLM classifier with record/replay.

Replay mode (default; used in tests and CI) reads cached predictions from a
committed CSV and never touches the network or needs an API key. Record mode
builds the same prompt and calls an injected `call_fn` (a thin provider wrapper),
then appends to the predictions file — the identical pipeline runs whether
responses are live or cached.

The committed predictions are retained only as deterministic test fixtures, not as
billed API calls or production catalogue labels. Token counts are estimated from the
prompt this module builds. Latency is not asserted in replay.

Responses are validated into `ProductFamily`, so an off-taxonomy reply is coerced
to 'OT' and can never inject an unknown label.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from commercial_intelligence.products.taxonomy import ProductFamily, taxonomy

# A provider call: (system_prompt, user_prompt, model) -> raw JSON string.
CallFn = Callable[[str, str, str], str]


def build_prompt(description: str) -> tuple[str, str]:
    t = taxonomy()
    lines = [f"{r.family_code}: {r.family} — {r.definition}" for r in t.itertuples()]
    system = (
        "You classify retail gift products into exactly one family from a fixed "
        'taxonomy. Reply with JSON only: {"family_code": "<CODE>", '
        '"confidence": <0-1>}. Use \'OT\' only if nothing else fits.\n\nTaxonomy:\n'
        + "\n".join(lines)
    )
    user = f'Product description: "{description}"\nReturn the JSON classification.'
    return system, user


def estimate_tokens(text: str) -> int:
    """Rough token count (~4 chars/token). Used for the estimated cost, not billing."""
    return max(1, round(len(text) / 4))


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0
    cost_usd: float = 0.0


@dataclass
class LLMClassifier:
    model: str
    predictions_path: Path
    usd_per_1m_input: float
    usd_per_1m_output: float
    est_output_tokens: int = 12
    mode: str = "replay"
    call_fn: CallFn | None = None
    _preds: dict[str, dict] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.predictions_path = Path(self.predictions_path)
        if self.mode == "replay":
            if not self.predictions_path.exists():
                raise FileNotFoundError(
                    f"Predictions {self.predictions_path} missing; record them first "
                    "(mode='record' with an API key) or run the baseline only."
                )
            with self.predictions_path.open() as f:
                for row in csv.DictReader(f):
                    self._preds[row["stock_code"]] = {
                        "family_code": row["family_code"],
                        "confidence": float(row["confidence"]),
                    }
        elif self.mode == "record":
            if self.call_fn is None:
                raise ValueError("record mode needs a call_fn (a provider wrapper).")
        else:
            raise ValueError(f"unknown mode {self.mode!r}")

    def _cost(self, in_tok: int, out_tok: int) -> float:
        return in_tok / 1e6 * self.usd_per_1m_input + out_tok / 1e6 * self.usd_per_1m_output

    def classify_one(self, stock_code: str, description: str) -> tuple[ProductFamily, Usage]:
        system, user = build_prompt(description)
        in_tok = estimate_tokens(system + user)

        if self.mode == "replay":
            entry = self._preds.get(stock_code)
            if entry is None:
                raise KeyError(f"{stock_code} not in predictions file")
            fam = ProductFamily(
                stock_code=stock_code,
                family_code=entry["family_code"],
                confidence=entry["confidence"],
            )
            out_tok = self.est_output_tokens
        else:  # record
            raw = self.call_fn(system, user, self.model)  # type: ignore[misc]
            payload = json.loads(raw)
            fam = ProductFamily(
                stock_code=stock_code,
                family_code=payload.get("family_code", "OT"),
                confidence=float(payload.get("confidence", 1.0)),
            )
            out_tok = estimate_tokens(raw)
            self._preds[stock_code] = {
                "family_code": fam.family_code, "confidence": fam.confidence
            }

        usage = Usage(in_tok, out_tok, 1, self._cost(in_tok, out_tok))
        return fam, usage

    def classify_frame(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Usage]:
        preds, total = [], Usage()
        for row in df.itertuples(index=False):
            fam, u = self.classify_one(row.stock_code, row.description)
            preds.append(
                {"stock_code": row.stock_code, "llm_code": fam.family_code,
                 "llm_confidence": fam.confidence}
            )
            total.input_tokens += u.input_tokens
            total.output_tokens += u.output_tokens
            total.calls += 1
        total.cost_usd = self._cost(total.input_tokens, total.output_tokens)
        return pd.DataFrame(preds), total

    def save_predictions(self) -> None:
        self.predictions_path.parent.mkdir(parents=True, exist_ok=True)
        with self.predictions_path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["stock_code", "family_code", "confidence"])
            for sc in sorted(self._preds):
                e = self._preds[sc]
                w.writerow([sc, e["family_code"], e["confidence"]])


def from_settings(settings: dict, call_fn: CallFn | None = None) -> LLMClassifier:
    llm = settings["products"]["llm"]
    from commercial_intelligence.common.config import repo_path

    return LLMClassifier(
        model=llm["model"],
        predictions_path=repo_path(llm["predictions_path"]),
        usd_per_1m_input=float(llm["usd_per_1m_input_tokens"]),
        usd_per_1m_output=float(llm["usd_per_1m_output_tokens"]),
        est_output_tokens=int(llm["est_output_tokens"]),
        mode=llm["mode"],
        call_fn=call_fn,
    )
