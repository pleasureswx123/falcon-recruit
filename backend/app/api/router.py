"""API 路由聚合。

所有业务端点统一在此挂载，通过 include_router 注入到主应用。
"""
from fastapi import APIRouter

from app.api.endpoints import (
    candidates,
    dashboard,
    export,
    files,
    health,
    jobs,
    tasks,
)

api_router = APIRouter(prefix="/api")

# Phase 1: 健康检查
api_router.include_router(health.router)

# Phase 2: 职位管理
api_router.include_router(jobs.router, prefix="/jobs")

# Phase 3: 分拣引擎
api_router.include_router(tasks.router, prefix="/tasks")
api_router.include_router(candidates.router, prefix="/candidates")
api_router.include_router(files.router, prefix="/files")

# Phase 5: 批量导出 + 概览统计
api_router.include_router(export.router, prefix="/export")
api_router.include_router(dashboard.router, prefix="/dashboard")
