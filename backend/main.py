"""猎鹰 Falcon AI · 后端入口。

启动命令（开发环境）:
    uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import dispose_db, init_db
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.rate_limit import attach_rate_limiter

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # 生产环境不自动 create_all，应通过 alembic upgrade head 管理 schema
    if settings.debug or settings.database_url.startswith("sqlite"):
        await init_db()
    else:
        logger.info("skip create_all in production - use alembic instead")
    # 打印鉴权模式，便于运维确认
    if not settings.falcon_api_key:
        logger.warning(
            "FALCON_API_KEY not set: API is running in OPEN mode (dev/smoke only)"
        )
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
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
