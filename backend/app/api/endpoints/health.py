"""健康检查端点。

用于前端探测后端服务可用性。
"""
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    app_name: str
    app_env: str
    app_version: str
    server_time: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        app_env=settings.app_env,
        app_version=settings.app_version,
        server_time=datetime.now(timezone.utc).isoformat(),
    )
