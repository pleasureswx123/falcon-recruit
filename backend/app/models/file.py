"""文件附件数据模型 (TDD §2.3)。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlmodel import Field, SQLModel


class FileType(str, Enum):
    """文件业务类型。"""

    RESUME = "RESUME"
    PORTFOLIO = "PORTFOLIO"
    UNKNOWN = "UNKNOWN"


class ParseStatus(str, Enum):
    """文本解析状态。"""

    PENDING = "pending"
    PARSED = "parsed"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


def _uuid_str() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ResumeFile(SQLModel, table=True):
    """文件附件表。使用 ResumeFile 命名以避免与内置 File 冲突。"""

    __tablename__ = "files"

    id: str = Field(
        default_factory=_uuid_str,
        sa_column=Column(String(36), primary_key=True, index=True),
    )
    task_id: str = Field(
        sa_column=Column(
            String(36),
            ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    job_id: str = Field(
        sa_column=Column(
            String(36),
            ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    candidate_id: str | None = Field(
        default=None,
        sa_column=Column(
            String(36),
            ForeignKey("candidates.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )
    file_type: FileType = Field(
        default=FileType.UNKNOWN,
        sa_column=Column(String(16), nullable=False, index=True),
    )
    original_name: str = Field(sa_column=Column(String(512), nullable=False))
    new_name: str | None = Field(
        default=None, sa_column=Column(String(256), nullable=True)
    )
    file_path: str = Field(sa_column=Column(String(1024), nullable=False))
    mime: str | None = Field(default=None, sa_column=Column(String(128), nullable=True))
    size: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    parse_status: ParseStatus = Field(
        default=ParseStatus.PENDING,
        sa_column=Column(String(16), nullable=False, index=True),
    )
    parse_error: str | None = Field(
        default=None, sa_column=Column(String(512), nullable=True)
    )
    text_excerpt: str | None = Field(
        default=None, sa_column=Column(String(2048), nullable=True)
    )
    zip_member: str = Field(sa_column=Column(String(1024), nullable=False))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
