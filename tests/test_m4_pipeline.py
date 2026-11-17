"""M4 end-to-end: only the independently evaluated baseline is publishable."""

from __future__ import annotations

from commercial_intelligence.products import report as m4
from commercial_intelligence.products.taxonomy import family_codes


def test_pipeline_runs_and_chooses_a_method(con):
    out = m4.run(con)
    assert out.chosen == "baseline"
    assert 0.0 <= out.baseline_scores["macro_f1"] <= 1.0
    assert out.baseline_scores["n"] == int((out.gold["split"] == "test").sum())


def test_catalogue_fully_labelled_with_valid_families(con):
    out = m4.run(con)
    assert len(out.catalogue) > 0
    assert set(out.catalogue["family_code"]).issubset(set(family_codes()))
    assert out.catalogue["family_code"].notna().all()
    assert set(out.catalogue["family_source"]) == {"baseline"}


def test_no_llm_metric_is_published(con):
    out = m4.run(con)
    report = m4.render_report(out)
    assert "previous LLM score has been withdrawn" in report
    assert "0.963" not in report


def test_export_removes_withdrawn_llm_artifacts(con, tmp_path):
    out = m4.run(con)
    stale = [
        tmp_path / f"{stem}{suffix}"
        for stem in ("per_class_llm", "confusion_llm", "errors_llm")
        for suffix in (".csv", ".parquet")
    ]
    for path in stale:
        path.write_text("withdrawn", encoding="utf-8")

    m4.write_exports(out, tmp_path)

    assert not any(path.exists() for path in stale)
