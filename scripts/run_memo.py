"""M7 runner: generate the commercial memo, KPI tree and PRD from pipeline numbers.

Usage:
    python scripts/run_memo.py
Requires the milestone exports (M2–M6).
"""

from __future__ import annotations

import sys

from commercial_intelligence.common.config import repo_path
from commercial_intelligence.reporting import exports, memo


def main() -> int:
    try:
        n = memo.memo_numbers()
    except exports.MissingExportError as e:
        print(f"{e}", file=sys.stderr)
        return 1

    outputs = {
        "docs/commercial_memo.md": memo.render_memo(n),
        "docs/kpi_tree.md": memo.render_kpi_tree(n),
        "docs/prd_pricing_experimentation.md": memo.render_prd(n),
    }
    for rel, text in outputs.items():
        path = repo_path(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
