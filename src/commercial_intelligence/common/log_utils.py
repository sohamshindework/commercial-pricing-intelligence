"""Small structured-logging helper: `event key=value ...` lines."""

from __future__ import annotations

import logging

_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def get_logger(name: str) -> logging.Logger:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format=_FORMAT)
    return logging.getLogger(name)


def kv(event: str, **fields: object) -> str:
    """Format an event with key=value pairs, e.g. kv('step_done', step='stg', rows=10)."""
    parts = [event] + [f"{k}={v}" for k, v in fields.items()]
    return " ".join(parts)
