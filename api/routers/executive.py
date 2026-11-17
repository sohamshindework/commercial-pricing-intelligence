"""Executive decisions: prioritised recommendations assembled from pipeline numbers."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas import (
    ExecHeadline,
    ExecutiveResponse,
    MonitoringKpi,
    Recommendation,
)
from commercial_intelligence.reporting import exports, memo

router = APIRouter(prefix="/api/executive", tags=["executive"])


@router.get("/summary", response_model=ExecutiveResponse)
def summary() -> ExecutiveResponse:
    try:
        s = memo.executive_summary()
    except exports.MissingExportError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return ExecutiveResponse(
        situation=s["situation"],
        headline=ExecHeadline(**s["headline"]),
        recommendations=[Recommendation(**r) for r in s["recommendations"]],
        monitoring_kpis=[MonitoringKpi(**k) for k in s["monitoring_kpis"]],
        limitations=s["limitations"],
    )
