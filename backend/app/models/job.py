"""职位数据模型 (TDD §2.1)。

设计说明：
- id 用 String(36) 存储 UUID 字符串，兼容 PostgreSQL 类型系统。
- criteria 用 SQLAlchemy JSON 列，PostgreSQL 下自动使用 JSONB 类型（支持索引与高效查询）。
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime, String
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class JobStatus(str, Enum):
    """职位状态枚举。"""

    ACTIVE = "active"
    CLOSED = "closed"


def _uuid_str() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Job(SQLModel, table=True):
    """职位表。对应 TDD §2.1 Jobs。"""

    __tablename__ = "jobs"

    id: str = Field(
        default_factory=_uuid_str,
        sa_column=Column(String(36), primary_key=True, index=True),
    )
    title: str = Field(sa_column=Column(String(120), nullable=False, index=True))
    raw_jd: str = Field(sa_column=Column(String, nullable=False))
    criteria: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    status: JobStatus = Field(
        default=JobStatus.ACTIVE,
        sa_column=Column(String(16), nullable=False, index=True),
    )
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
