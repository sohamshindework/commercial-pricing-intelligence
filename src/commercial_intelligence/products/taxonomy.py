"""Load the product-family taxonomy and gold labels; Pydantic schema for LLM output."""

from __future__ import annotations

from functools import cache

import pandas as pd
from pydantic import BaseModel, Field, field_validator

from commercial_intelligence.common.config import load_settings, repo_path


@cache
def taxonomy() -> pd.DataFrame:
    df = pd.read_csv(repo_path(load_settings()["products"]["taxonomy_path"]))
    return df


@cache
def family_codes() -> tuple[str, ...]:
    return tuple(taxonomy()["family_code"])


@cache
def code_to_name() -> dict[str, str]:
    t = taxonomy()
    return dict(zip(t["family_code"], t["family"], strict=True))


def load_gold() -> pd.DataFrame:
    df = pd.read_csv(repo_path(load_settings()["products"]["gold_path"]), dtype={"stock_code": str})
    return df


class ProductFamily(BaseModel):
    """Validated structured output for one product classification.

    The LLM must return a code from the fixed taxonomy; anything else is coerced
    to 'OT' (Other / Unsure) by the validator so a bad response can never inject
    a new label.
    """

    stock_code: str
    family_code: str = Field(description="One taxonomy code, e.g. KD, HD, BG …")
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)

    @field_validator("family_code")
    @classmethod
    def _known_code(cls, v: str) -> str:
        return v if v in family_codes() else "OT"
