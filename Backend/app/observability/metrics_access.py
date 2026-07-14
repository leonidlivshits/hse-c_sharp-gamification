from __future__ import annotations

from fastapi import HTTPException, status

from app.core.config import settings


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return None
    token = authorization[len(prefix):].strip()
    return token or None


def ensure_metrics_access(
    x_metrics_token: str | None = None,
    authorization: str | None = None,
) -> None:
    expected_token = settings.get_monitoring_metrics_token()
    if not expected_token:
        if settings.app_env.lower() == "test":
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metrics token is not configured",
        )

    provided_token = x_metrics_token or _bearer_token(authorization)
    if provided_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Metrics access denied",
        )
