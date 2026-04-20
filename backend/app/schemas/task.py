"""分拣任务相关 DTO。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskStatus


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    status: TaskStatus
    stage_message: str | None
    progress: int
    total_files: int
    parsed_files: int
    failed_files: int
    candidate_count: int
    source_zip_name: str
    source_zip_size: int
    error_message: str | None
    diagnostics: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None


class TaskListResponse(BaseModel):
    total: int
    items: list[TaskRead]
