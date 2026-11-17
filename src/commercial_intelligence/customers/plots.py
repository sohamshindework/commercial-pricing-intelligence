"""Matplotlib figures for the memo: CLV calibration and cohort-retention heatmap.

Light theme to match the project's visual identity (ivory background, muted
indigo / sage). Figures are written as PNG; the web app and memo use them directly or redraw from
the same exported tables.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

INK = "#2e3440"
INDIGO = "#4c566a"
SAGE = "#8aa399"
CORAL = "#d08c74"
IVORY = "#faf8f3"


def _style(ax: plt.Axes) -> None:
    ax.set_facecolor(IVORY)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(colors=INK)
    ax.yaxis.label.set_color(INK)
    ax.xaxis.label.set_color(INK)
    ax.title.set_color(INK)


def calibration_plot(cal_table: pd.DataFrame, out_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=130)
    fig.patch.set_facecolor(IVORY)
    x = cal_table["freq_bucket"]
    ax.plot(x, cal_table["actual"], "o-", color=INK, label="Actual", linewidth=2)
    ax.plot(x, cal_table["bgnbd"], "s--", color=INDIGO, label="BG/NBD predicted")
    ax.plot(x, cal_table["baseline"], "^:", color=CORAL, label="Baseline predicted")
    ax.set_xlabel("Purchases in calibration period (capped at 8)")
    ax.set_ylabel("Mean purchases in holdout")
    ax.set_title("CLV calibration: predicted vs actual holdout purchases")
    ax.legend(frameon=False)
    _style(ax)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def retention_heatmap(rates: pd.DataFrame, out_path: Path, max_offset: int = 12) -> Path:
    offsets = [o for o in rates.columns if isinstance(o, int) and 0 <= o <= max_offset]
    data = rates[offsets]
    fig, ax = plt.subplots(figsize=(9, 6), dpi=130)
    fig.patch.set_facecolor(IVORY)
    im = ax.imshow(data.to_numpy(dtype=float), aspect="auto", cmap="YlGnBu", vmin=0, vmax=0.5)
    ax.set_xticks(range(len(offsets)))
    ax.set_xticklabels(offsets)
    ax.set_yticks(range(len(data.index)))
    ax.set_yticklabels([str(d)[:7] for d in data.index], fontsize=7)
    ax.set_xlabel("Months since first purchase")
    ax.set_ylabel("Cohort (first-purchase month)")
    ax.set_title("Monthly cohort retention")
    fig.colorbar(im, ax=ax, label="Share of cohort active")
    _style(ax)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    return out_path
