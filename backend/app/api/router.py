"""API 路由聚合。

所有业务端点统一在此挂载，通过 include_router 注入到主应用。
鉴权：使用 Session + Cookie 认证（/health 和 /auth 除外）。
"""
from fastapi import APIRouter, Depends

from app.api.endpoints import (
    auth,
    candidates,
    dashboard,
    export,
    files,
    health,
    jobs,
    tasks,
)
from app.core.auth import get_current_user

api_router = APIRouter(prefix="/api")

# Phase 1: 健康检查（无鉴权，供容器 healthcheck / 监控探活）
api_router.include_router(health.router)

# Phase 6: 认证路由（无需鉴权）
api_router.include_router(auth.router, prefix="/auth")

# 以下业务路由统一挂 Session 认证依赖
_auth = [Depends(get_current_user)]

# Phase 2: 职位管理
api_router.include_router(jobs.router, prefix="/jobs", dependencies=_auth)

# Phase 3: 分拣引擎
api_router.include_router(tasks.router, prefix="/tasks", dependencies=_auth)
api_router.include_router(candidates.router, prefix="/candidates", dependencies=_auth)
api_router.include_router(files.router, prefix="/files", dependencies=_auth)

# Phase 5: 批量导出 + 概览统计
api_router.include_router(export.router, prefix="/export", dependencies=_auth)
api_router.include_router(dashboard.router, prefix="/dashboard", dependencies=_auth)
