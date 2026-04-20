"""数据库连接与会话管理。

使用 SQLModel(基于 SQLAlchemy 2.0) 的异步引擎。
默认 SQLite + aiosqlite，开发零配置；生产可在 .env 切换为 PostgreSQL+asyncpg。
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import get_settings

_settings = get_settings()

# SQLite 在 async 模式下需要 check_same_thread=False
_connect_args: dict = {}
if _settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_async_engine(
    _settings.database_url,
    echo=_settings.database_echo,
    future=True,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    """启动时自动建表（开发期便利，生产应改用 Alembic）。"""
    # 触发所有 SQLModel 表元数据注册
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def dispose_db() -> None:
    """关闭时释放连接池。"""
    await engine.dispose()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：提供数据库会话。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# 便于在路由签名里复用
SessionDep = Annotated[AsyncSession, Depends(get_session)]
