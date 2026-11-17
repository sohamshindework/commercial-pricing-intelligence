"""Guard against recreating the retired, label-derived LLM cassette.

The original development helper copied gold labels into a replay file and could
not support an independent evaluation. It is intentionally disabled. A future
LLM comparison must use provider responses recorded without exposing gold test
labels, with model/version, request IDs and timestamps retained for provenance.
"""

from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "Disabled: the former cassette was derived from gold labels. "
        "Use an independently implemented provider recording workflow that never "
        "passes test labels to the classifier."
    )


if __name__ == "__main__":
    main()
