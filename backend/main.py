"""猎鹰 Falcon AI · 后端入口。

启动命令（开发环境）:
    uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import dispose_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：初始化数据库（自动建表，开发期便利）
    await init_db()
    yield
    # 关闭：释放连接池
    await dispose_db()


def create_app() -> FastAPI:
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
    )

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
