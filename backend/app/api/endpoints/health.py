"""健康检查端点。

- /api/health      liveness：进程存活即可（无鉴权，适合容器 healthcheck）。
- /api/health/ready readiness：探 DB + Redis，失败返回 503。
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    app_name: str
    app_env: str
    app_version: str
    server_time: str


class ReadinessComponent(BaseModel):
    name: str
    ok: bool
    detail: str | None = None


class ReadinessResponse(BaseModel):
    status: str
    components: list[ReadinessComponent]
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


async def _probe_db() -> ReadinessComponent:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return ReadinessComponent(name="database", ok=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("db probe failed: %s", exc)
        return ReadinessComponent(name="database", ok=False, detail=str(exc)[:200])


async def _probe_redis() -> ReadinessComponent | None:
    settings = get_settings()
    if not settings.redis_url:
        return None
    try:
        from redis import asyncio as aioredis  # 延迟导入，未装 redis 时不影响模块加载
        client = aioredis.from_url(settings.redis_url, socket_timeout=3)
        try:
            pong = await client.ping()
            return ReadinessComponent(name="redis", ok=bool(pong))
        finally:
            await client.aclose()
    except Exception as exc:  # noqa: BLE001
        logger.warning("redis probe failed: %s", exc)
        return ReadinessComponent(name="redis", ok=False, detail=str(exc)[:200])


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness(response: Response) -> ReadinessResponse:
    components: list[ReadinessComponent] = [await _probe_db()]
    redis_comp = await _probe_redis()
    if redis_comp is not None:
        components.append(redis_comp)

    all_ok = all(c.ok for c in components)
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ok" if all_ok else "degraded",
        components=components,
        server_time=datetime.now(timezone.utc).isoformat(),
    )
