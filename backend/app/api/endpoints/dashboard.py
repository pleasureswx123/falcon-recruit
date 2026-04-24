"""Dashboard 概览 API (Phase 5)。

端点：
- GET /api/dashboard/overview           一次性返回统计 + 高分人才 + 最近任务
- GET /api/dashboard/stats              仅返回数值统计
- GET /api/dashboard/top-candidates     评分最高候选人列表
- GET /api/dashboard/recent-tasks       最近分拣任务
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionDep
from app.core.auth import get_current_user
from app.models.candidate import Candidate
from app.models.job import Job, JobStatus
from app.models.task import SortingTask, TaskStatus
from app.models.user import User
from app.schemas.dashboard import (
    DashboardOverview,
    DashboardStats,
    RecentTask,
    TopCandidate,
)

router = APIRouter(tags=["dashboard"])

_HIGH_SCORE_THRESHOLD = 80
_RUNNING_STATUSES = (
    TaskStatus.PENDING,
    TaskStatus.EXTRACTING,
    TaskStatus.PARSING,
    TaskStatus.LINKING,
)


async def _compute_stats(session: AsyncSession, owner_id: int) -> DashboardStats:
    async def count(stmt) -> int:
        result = await session.execute(stmt)
        return int(result.scalar_one() or 0)

    # 所有统计都基于当前用户的职位进行过滤
    jobs_total = await count(
        select(func.count()).select_from(Job).where(Job.owner_id == owner_id)
    )
    jobs_active = await count(
        select(func.count())
        .select_from(Job)
        .where(Job.owner_id == owner_id)
        .where(Job.status == JobStatus.ACTIVE)
    )
    
    # 通过 JOIN Job 过滤候选人
    candidates_total = await count(
        select(func.count())
        .select_from(Candidate)
        .join(Job, Candidate.job_id == Job.id)
        .where(Job.owner_id == owner_id)
    )
    candidates_unverified = await count(
        select(func.count())
        .select_from(Candidate)
        .join(Job, Candidate.job_id == Job.id)
        .where(Job.owner_id == owner_id)
        .where(Candidate.is_verified.is_(False))
    )
    high_score_count = await count(
        select(func.count())
        .select_from(Candidate)
        .join(Job, Candidate.job_id == Job.id)
        .where(Job.owner_id == owner_id)
        .where(Candidate.score.is_not(None))
        .where(Candidate.score >= _HIGH_SCORE_THRESHOLD)
    )
    
    # 通过 JOIN Job 过滤任务
    tasks_running = await count(
        select(func.count())
        .select_from(SortingTask)
        .join(Job, SortingTask.job_id == Job.id)
        .where(Job.owner_id == owner_id)
        .where(SortingTask.status.in_(_RUNNING_STATUSES))
    )

    return DashboardStats(
        jobs_total=jobs_total,
        jobs_active=jobs_active,
        candidates_total=candidates_total,
        candidates_unverified=candidates_unverified,
        high_score_count=high_score_count,
        tasks_running=tasks_running,
    )


async def _load_top_candidates(
    session: AsyncSession, owner_id: int, limit: int
) -> list[TopCandidate]:
    stmt = (
        select(Candidate, Job.title)
        .join(Job, Job.id == Candidate.job_id, isouter=True)
        .where(Job.owner_id == owner_id)
        .where(Candidate.score.is_not(None))
        .order_by(Candidate.score.desc(), Candidate.updated_at.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    items: list[TopCandidate] = []
    for cand, job_title in rows:
        items.append(
            TopCandidate(
                id=cand.id,
                job_id=cand.job_id,
                job_title=job_title,
                name=cand.name,
                score=cand.score,
                phone=cand.phone,
                email=cand.email,
                is_verified=cand.is_verified,
                updated_at=cand.updated_at,
            )
        )
    return items


async def _load_recent_tasks(
    session: AsyncSession, owner_id: int, limit: int
) -> list[RecentTask]:
    stmt = (
        select(SortingTask, Job.title)
        .join(Job, Job.id == SortingTask.job_id, isouter=True)
        .where(Job.owner_id == owner_id)
        .order_by(SortingTask.created_at.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    items: list[RecentTask] = []
    for task, job_title in rows:
        items.append(
            RecentTask(
                id=task.id,
                job_id=task.job_id,
                job_title=job_title,
                status=task.status,
                progress=task.progress,
                stage_message=task.stage_message,
                total_files=task.total_files,
                parsed_files=task.parsed_files,
                failed_files=task.failed_files,
                candidate_count=task.candidate_count,
                source_zip_name=task.source_zip_name,
                created_at=task.created_at,
                finished_at=task.finished_at,
            )
        )
    return items


@router.get("/overview", response_model=DashboardOverview, summary="首页一次性概览")
async def get_overview(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
    top_limit: int = Query(default=10, ge=1, le=50),
    recent_limit: int = Query(default=5, ge=1, le=20),
) -> DashboardOverview:
    stats = await _compute_stats(session, owner_id=current_user.id)
    top = await _load_top_candidates(session, owner_id=current_user.id, limit=top_limit)
    recent = await _load_recent_tasks(session, owner_id=current_user.id, limit=recent_limit)
    return DashboardOverview(stats=stats, top_candidates=top, recent_tasks=recent)


@router.get("/stats", response_model=DashboardStats, summary="概览数值统计")
async def get_stats(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> DashboardStats:
    return await _compute_stats(session, owner_id=current_user.id)


@router.get(
    "/top-candidates",
    response_model=list[TopCandidate],
    summary="Top N 高分候选人",
)
async def get_top_candidates(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=10, ge=1, le=50),
) -> list[TopCandidate]:
    return await _load_top_candidates(session, owner_id=current_user.id, limit=limit)


@router.get(
    "/recent-tasks",
    response_model=list[RecentTask],
    summary="最近分拣任务",
)
async def get_recent_tasks(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=5, ge=1, le=20),
) -> list[RecentTask]:
    return await _load_recent_tasks(session, owner_id=current_user.id, limit=limit)
