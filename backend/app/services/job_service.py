"""职位业务逻辑层。"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobCriteria, JobUpdate
from app.services.jd_parser import parse_jd_to_criteria_async


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def create_job(session: AsyncSession, payload: JobCreate, owner_id: int) -> Job:
    """创建职位；若未显式提供 criteria，则由 jd_parser 自动解析（LLM 优先，规则式降级）。"""
    criteria: JobCriteria = payload.criteria or await parse_jd_to_criteria_async(
        payload.raw_jd, title_hint=payload.title
    )

    job = Job(
        owner_id=owner_id,
        title=payload.title.strip(),
        raw_jd=payload.raw_jd,
        criteria=criteria.model_dump(mode="json"),
        status=payload.status,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_job(session: AsyncSession, job_id: str, owner_id: int | None = None) -> Job | None:
    """获取职位详情，可选验证归属。"""
    job = await session.get(Job, job_id)
    if job and owner_id is not None and job.owner_id != owner_id:
        return None  # 无权访问
    return job


async def list_jobs(
    session: AsyncSession,
    owner_id: int,
    *,
    status: JobStatus | None = None,
    keyword: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[int, list[Job]]:
    """列表查询，返回 (总数, 当前页)。只返回当前用户的职位。"""
    base = select(Job).where(Job.owner_id == owner_id)
    if status is not None:
        base = base.where(Job.status == status)
    if keyword:
        kw = f"%{keyword.strip()}%"
        base = base.where(Job.title.ilike(kw))

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    rows_stmt = base.order_by(Job.created_at.desc()).offset(offset).limit(limit)
    rows = (await session.execute(rows_stmt)).scalars().all()
    return total, list(rows)


async def update_job(
    session: AsyncSession, job: Job, payload: JobUpdate, owner_id: int
) -> Job:
    """部分更新。"""
    # 验证归属
    if job.owner_id != owner_id:
        raise ValueError("无权修改该职位")
    
    data = payload.model_dump(exclude_unset=True)

    if "title" in data and data["title"] is not None:
        job.title = data["title"].strip()
    if "raw_jd" in data and data["raw_jd"] is not None:
        job.raw_jd = data["raw_jd"]
    if "criteria" in data and data["criteria"] is not None:
        criteria = payload.criteria  # 已是 JobCriteria 实例
        job.criteria = criteria.model_dump(mode="json")
    if "status" in data and data["status"] is not None:
        job.status = data["status"]

    job.updated_at = _utcnow()
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def delete_job(session: AsyncSession, job: Job) -> None:
    await session.delete(job)
    await session.commit()
