"""候选人数据模型 (TDD §2.2)。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


def _uuid_str() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Candidate(SQLModel, table=True):
    """候选人表。一人一岗，手机号 / 邮箱作为 PII 唯一键（在同职位下）。"""

    __tablename__ = "candidates"

    id: str = Field(
        default_factory=_uuid_str,
        sa_column=Column(String(36), primary_key=True, index=True),
    )
    job_id: str = Field(
        sa_column=Column(
            String(36),
            ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    name: str | None = Field(
        default=None, sa_column=Column(String(64), nullable=True, index=True)
    )
    phone: str | None = Field(
        default=None, sa_column=Column(String(32), nullable=True, index=True)
    )
    email: str | None = Field(
        default=None, sa_column=Column(String(128), nullable=True, index=True)
    )
    wechat: str | None = Field(
        default=None, sa_column=Column(String(64), nullable=True)
    )
    score: int | None = Field(
        default=None, sa_column=Column(Integer, nullable=True, index=True)
    )
    report: dict = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
