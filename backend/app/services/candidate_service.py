"""候选人业务逻辑层。"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.file import ResumeFile
from app.schemas.candidate import CandidateUpdate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def list_candidates(
    session: AsyncSession,
    *,
    job_id: str | None = None,
    keyword: str | None = None,
    verified: bool | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[int, list[Candidate]]:
    base = select(Candidate)
    if job_id:
        base = base.where(Candidate.job_id == job_id)
    if verified is not None:
        base = base.where(Candidate.is_verified == verified)
    if keyword:
        kw = f"%{keyword.strip()}%"
        base = base.where(
            or_(
                Candidate.name.ilike(kw),
                Candidate.phone.ilike(kw),
                Candidate.email.ilike(kw),
            )
        )

    total = (await session.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one()

    rows_stmt = (
        base.order_by(Candidate.created_at.desc()).offset(offset).limit(limit)
    )
    rows = (await session.execute(rows_stmt)).scalars().all()
    return total, list(rows)


async def get_candidate(session: AsyncSession, candidate_id: str) -> Candidate | None:
    return await session.get(Candidate, candidate_id)


async def get_candidate_files(
    session: AsyncSession, candidate_id: str
) -> list[ResumeFile]:
    stmt = (
        select(ResumeFile)
        .where(ResumeFile.candidate_id == candidate_id)
        .order_by(ResumeFile.file_type.asc(), ResumeFile.created_at.asc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def update_candidate(
    session: AsyncSession, candidate: Candidate, payload: CandidateUpdate
) -> Candidate:
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        if v is not None or k == "is_verified":
            setattr(candidate, k, v)
    candidate.updated_at = _utcnow()
    session.add(candidate)
    await session.commit()
    await session.refresh(candidate)
    return candidate


async def reassign_file(
    session: AsyncSession, file: ResumeFile, target_candidate: Candidate
) -> ResumeFile:
    """将单个文件改挂到另一个候选人（手动纠偏）。"""
    if file.job_id != target_candidate.job_id:
        raise ValueError("文件与目标候选人不属于同一职位")
    file.candidate_id = target_candidate.id
    session.add(file)
    await session.commit()
    await session.refresh(file)
    return file


async def get_file(session: AsyncSession, file_id: str) -> ResumeFile | None:
    return await session.get(ResumeFile, file_id)
