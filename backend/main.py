"""猎鹰 Falcon AI · 后端入口。

启动命令（开发环境）:
    uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import dispose_db, init_db
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.rate_limit import attach_rate_limiter

logger = logging.getLogger(__name__)


async def _reconcile_stale_tasks() -> None:
    """重启兜底：把所有卡在非终态的任务标记为 failed，避免"僵尸任务"。

    `asyncio.create_task()` 启动的后台协程在进程重启时会被直接杀死，
    但 DB 中的 status 不会被回写，前端会看到任务永远停留在 linking/parsing。
    """
    from datetime import datetime, timezone

    from sqlalchemy import update as sqa_update

    from app.core.database import AsyncSessionLocal
    from app.models.task import SortingTask, TaskStatus

    non_terminal = [
        TaskStatus.PENDING,
        TaskStatus.EXTRACTING,
        TaskStatus.PARSING,
        TaskStatus.LINKING,
    ]
    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)
        stmt = (
            sqa_update(SortingTask)
            .where(SortingTask.status.in_(non_terminal))
            .values(
                status=TaskStatus.FAILED,
                error_message="服务重启导致任务中断",
                stage_message="已中断",
                finished_at=now,
                updated_at=now,
            )
        )
        result = await session.execute(stmt)
        await session.commit()
        if result.rowcount:
            logger.warning("reconciled %d stale tasks as failed", result.rowcount)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # 生产环境不自动 create_all，应通过 alembic upgrade head 管理 schema
    if settings.debug:
        await init_db()
    else:
        logger.info("skip create_all in production - use alembic instead")
    # 清理因上次进程崩溃/重启遗留的僵尸任务
    await _reconcile_stale_tasks()
    yield
    await dispose_db()


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI 驱动的简历智能分拣与人岗匹配平台",
        debug=settings.debug,
        lifespan=lifespan,
    )

    register_exception_handlers(app)
    attach_rate_limiter(app)

    app.include_router(api_router)

    @app.get("/", tags=["root"])
    async def root():
        return {
            "app": settings.app_name,
            "env": settings.app_env,
            "version": settings.app_version,
            "docs": "/docs",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
