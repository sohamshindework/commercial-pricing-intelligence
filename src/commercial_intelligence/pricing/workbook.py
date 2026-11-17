"""Excel experiment-sizing workbook with LIVE formulas (openpyxl).

The computed cells contain Excel formulas, not baked numbers, so a user can
change the inputs (baseline mean/sd, MDE, alpha, power, weeks) and the sample
size, products per arm and duration recompute in Excel.
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill

from commercial_intelligence.pricing.experiment import ExperimentDesign, PowerResult

_HEADER = Font(bold=True, size=13)
_LABEL = Font(bold=True)
_INPUT_FILL = PatternFill("solid", fgColor="FBEFD9")
_CALC_FILL = PatternFill("solid", fgColor="E8EEE9")


def write_sizing_workbook(
    path: Path, power: PowerResult, design: ExperimentDesign, unadjusted_sd: float
) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Experiment sizing"
    ws.column_dimensions["A"].width = 74
    ws.column_dimensions["B"].width = 20

    ws["A1"] = "Pricing experiment — sample-size calculator"
    ws["A1"].font = _HEADER
    ws["A2"] = "SKU-randomised ANCOVA plan; edit the shaded inputs and Excel recomputes."
    ws["A2"].font = Font(italic=True, color="666666")

    inputs = [
        ("Baseline mean (average weekly gross sales revenue per SKU, GBP)",
         round(power.baseline_mean, 2)),
        ("Unadjusted SKU-outcome std dev", round(unadjusted_sd, 2)),
        ("Historical pre/post correlation", design.preperiod_correlation),
        ("Target minimum detectable effect (relative)", power.mde_relative),
        ("Alpha (two-sided)", power.alpha),
        ("Power (1 - beta)", power.power),
        ("Eligible SKUs", design.eligible_products),
        ("Experiment duration (weeks)", design.duration_weeks),
    ]
    r = 4
    for label, value in inputs:
        ws[f"A{r}"] = label
        ws[f"A{r}"].font = _LABEL
        ws[f"B{r}"] = value
        ws[f"B{r}"].fill = _INPUT_FILL
        r += 1

    # Cell map: mean B4, sd B5, rho B6, MDE B7, alpha B8, power B9,
    # eligible SKUs B10, duration B11.
    calcs = [
        ("CUPED/ANCOVA residual std dev", "=B5*SQRT(1-B6^2)"),
        ("Adjusted effect size (Cohen's d)", "=B7*B4/B13"),
        ("z(1 - alpha/2)", "=NORMSINV(1-B8/2)"),
        ("z(power)", "=NORMSINV(B9)"),
        ("Required SKUs per arm (normal approximation)", "=ROUNDUP(2*(B15+B16)^2/B14^2,0)"),
        ("Available SKUs per arm", "=INT(B10/2)"),
        ("MDE with available SKUs (adjusted)", "=SQRT(2)*(B15+B16)*B13/(B4*SQRT(B18))"),
        ("MDE with available SKUs (unadjusted)", "=SQRT(2)*(B15+B16)*B5/(B4*SQRT(B18))"),
        ("Adequately powered for target MDE?", '=IF(B18>=B17,"YES","NO")'),
        ("Total SKUs assigned", "=2*B18"),
    ]
    r = 13
    for label, formula in calcs:
        ws[f"A{r}"] = label
        ws[f"A{r}"].font = _LABEL
        ws[f"B{r}"] = formula
        ws[f"B{r}"].fill = _CALC_FILL
        r += 1

    for cell in ("B4", "B5", "B13"):
        ws[cell].number_format = '£#,##0.00'
    ws["B6"].number_format = "0.000"
    for cell in ("B7", "B8", "B9", "B19", "B20"):
        ws[cell].number_format = "0.0%"
    for cell in ("B10", "B11", "B17", "B18", "B22"):
        ws[cell].number_format = "#,##0"
    for cell in ("B14", "B15", "B16"):
        ws[cell].number_format = "0.000"
    ws.conditional_formatting.add(
        "B21",
        FormulaRule(
            formula=['B21="NO"'],
            fill=PatternFill("solid", fgColor="FCE8E6"),
            font=Font(bold=True, color="9C0006"),
        ),
    )

    note_row = r + 1
    notes = [
        "Notes:",
        "- SKU is the randomisation and analysis unit; repeated weeks are aggregated.",
        "- The primary metric includes zero-sales SKU-weeks.",
        "- Historical correlation is a planning assumption, not an experiment result.",
        "- Python uses a t-test solver; this sheet uses an independent normal approximation.",
        "- Observational price-response analysis is not causal.",
        "- Margin is scenario-only because cost data is unavailable.",
    ]
    for i, note in enumerate(notes):
        ws[f"A{note_row + i}"] = note
        ws[f"A{note_row + i}"].alignment = Alignment(wrap_text=False)

    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path
