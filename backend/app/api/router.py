"""API 路由聚合。

所有业务端点统一在此挂载，通过 include_router 注入到主应用。
鉴权：除 /health 外全部挂 require_api_key（未配置 FALCON_API_KEY 时自动放行）。
"""
from fastapi import APIRouter, Depends

from app.api.endpoints import (
    candidates,
    dashboard,
    export,
    files,
    health,
    jobs,
    tasks,
)
from app.core.security import require_api_key

api_router = APIRouter(prefix="/api")

# Phase 1: 健康检查（无鉴权，供容器 healthcheck / 监控探活）
api_router.include_router(health.router)

# 以下业务路由统一挂 API Key 依赖
_auth = [Depends(require_api_key)]

# Phase 2: 职位管理
api_router.include_router(jobs.router, prefix="/jobs", dependencies=_auth)

# Phase 3: 分拣引擎
api_router.include_router(tasks.router, prefix="/tasks", dependencies=_auth)
api_router.include_router(candidates.router, prefix="/candidates", dependencies=_auth)
api_router.include_router(files.router, prefix="/files", dependencies=_auth)

# Phase 5: 批量导出 + 概览统计
api_router.include_router(export.router, prefix="/export", dependencies=_auth)
api_router.include_router(dashboard.router, prefix="/dashboard", dependencies=_auth)
