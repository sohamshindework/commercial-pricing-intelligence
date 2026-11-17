"""Load the versioned pipeline configuration (config/settings.toml)."""

from __future__ import annotations

import tomllib
from functools import cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = REPO_ROOT / "config" / "settings.toml"
SQL_DIR = REPO_ROOT / "sql"


@cache
def load_settings() -> dict[str, Any]:
    with CONFIG_PATH.open("rb") as f:
        return tomllib.load(f)


def repo_path(relative: str) -> Path:
    """Resolve a path from settings.toml against the repository root."""
    return REPO_ROOT / relative
