"""候选人相关 DTO。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.file import FileType, ParseStatus


class CandidateFileRead(BaseModel):
    """候选人关联文件（详情页用）。"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    file_type: FileType
    original_name: str
    new_name: str | None
    mime: str | None
    size: int
    parse_status: ParseStatus
    parse_error: str | None = None
    text_excerpt: str | None = None
    zip_member: str


class CandidateRead(BaseModel):
    """候选人摘要。"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    name: str | None
    phone: str | None
    email: str | None
    wechat: str | None
    score: int | None
    report: dict = Field(default_factory=dict)
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class CandidateDetail(CandidateRead):
    """候选人详情 = 摘要 + 关联文件。"""

    files: list[CandidateFileRead] = Field(default_factory=list)


class CandidateListResponse(BaseModel):
    total: int
    items: list[CandidateRead]


class CandidateUpdate(BaseModel):
    """手动纠偏用。"""

    name: str | None = None
    phone: str | None = None
    email: str | None = None
    wechat: str | None = None
    is_verified: bool | None = None


class FileReassign(BaseModel):
    """将文件改挂到另一个候选人。"""

    target_candidate_id: str
