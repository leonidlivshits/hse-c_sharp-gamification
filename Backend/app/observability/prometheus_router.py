from __future__ import annotations

from fastapi import APIRouter, Header, Response

from app.observability.metrics_access import ensure_metrics_access
from app.observability.prometheus_metrics import CONTENT_TYPE_LATEST, prometheus_payload

router = APIRouter()


@router.get("/metrics", include_in_schema=False)
async def metrics(
    x_metrics_token: str | None = Header(default=None, alias="X-Metrics-Token"),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    ensure_metrics_access(x_metrics_token=x_metrics_token, authorization=authorization)
    return Response(content=await prometheus_payload(), media_type=CONTENT_TYPE_LATEST)
