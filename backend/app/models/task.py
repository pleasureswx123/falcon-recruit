"""异步分拣任务数据模型 (Phase 3)。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class TaskStatus(str, Enum):
    """分拣任务状态。"""

    PENDING = "pending"
    EXTRACTING = "extracting"   # 解压 ZIP
    PARSING = "parsing"         # 文本解析
    LINKING = "linking"         # PII 关联
    SUCCEEDED = "succeeded"
    FAILED = "failed"


def _uuid_str() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SortingTask(SQLModel, table=True):
    """分拣任务。每次上传一个 ZIP 对应一条记录。"""

    __tablename__ = "tasks"

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
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        sa_column=Column(String(16), nullable=False, index=True),
    )
    stage_message: str | None = Field(
        default=None, sa_column=Column(String(256), nullable=True)
    )
    progress: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    # 统计
    total_files: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    parsed_files: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    failed_files: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    candidate_count: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    # 来源
    source_zip_name: str = Field(sa_column=Column(String(512), nullable=False))
    source_zip_size: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    # 失败详情
    error_message: str | None = Field(
        default=None, sa_column=Column(String(1024), nullable=True)
    )
    # 诊断报告（例如每个 candidate 的关联理由）
    diagnostics: dict = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    finished_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
