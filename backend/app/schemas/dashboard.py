"""Dashboard DTO (Phase 5)。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskStatus


class DashboardStats(BaseModel):
    """首页概览统计。"""

    jobs_total: int
    jobs_active: int
    candidates_total: int
    candidates_unverified: int
    high_score_count: int  # score >= 80
    tasks_running: int


class TopCandidate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    job_title: str | None = None
    name: str | None
    score: int | None
    phone: str | None
    email: str | None
    is_verified: bool
    updated_at: datetime


class RecentTask(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    job_title: str | None = None
    status: TaskStatus
    progress: int
    stage_message: str | None
    total_files: int
    parsed_files: int
    failed_files: int
    candidate_count: int
    source_zip_name: str
    created_at: datetime
    finished_at: datetime | None = None


class DashboardOverview(BaseModel):
    stats: DashboardStats
    top_candidates: list[TopCandidate] = Field(default_factory=list)
    recent_tasks: list[RecentTask] = Field(default_factory=list)
