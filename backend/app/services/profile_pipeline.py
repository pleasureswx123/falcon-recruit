"""画像评分总流水线：profile -> verify -> score -> interview -> 写入 Candidate.report。

被 zip_processor 在分拣完成后批量调用；也作为独立接口供 "重新评估" 场景使用。
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.file import FileType, ParseStatus, ResumeFile
from app.models.job import Job
from app.schemas.job import JobCriteria
from app.schemas.profile import CandidateReport, ResumeProfile
from app.services import file_parser as fp
from app.services.interview_advisor import generate_questions_async
from app.services.pii_extractor import extract_pii
from app.services.resume_parser import parse_resume_async
from app.services.resume_verifier import verify_profile
from app.services.scoring_engine import (
    compose_strengths_weaknesses,
    score_candidate_async,
)

logger = logging.getLogger(__name__)


async def _load_resume_text(
    session: AsyncSession, candidate: Candidate
) -> tuple[str, ResumeProfile | None]:
    """取该候选人的简历文件，重新解析成纯文本。"""
    stmt = (
        select(ResumeFile)
        .where(ResumeFile.candidate_id == candidate.id)
        .order_by(ResumeFile.file_type.asc(), ResumeFile.created_at.asc())
    )
    files = list((await session.execute(stmt)).scalars().all())
    if not files:
        return "", None

    # 优先选简历；若无简历则选第一个 PARSED 的文件
    primary = next(
        (f for f in files if f.file_type == FileType.RESUME), None
    ) or next(
        (f for f in files if f.parse_status == ParseStatus.PARSED), None
    )
    if primary is None:
        return "", None

    if not os.path.exists(primary.file_path):
        return primary.text_excerpt or "", None

    try:
        data = _read_bytes(primary.file_path)
        result = fp.parse_file(data, primary.original_name)
        if result.status == ParseStatus.PARSED and result.text:
            return result.text, None
    except Exception as exc:  # noqa: BLE001
        logger.warning("reparse resume failed %s: %s", primary.file_path, exc)

    # 兜底：text_excerpt
    return primary.text_excerpt or "", None


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


async def _build_report_async(
    text: str,
    criteria: JobCriteria,
    job_title: str,
    fallback_name: str | None,
) -> CandidateReport:
    profile = await parse_resume_async(text, fallback_name=fallback_name)
    if not profile.name and fallback_name:
        profile.name = fallback_name
    # 用 regex 提取的 PII 兜底 LLM 画像缺失（PII 以正则为准，更稳定）
    pii = extract_pii(text)
    if not profile.phone and pii.phones:
        profile.phone = pii.phones[0]
    if not profile.email and pii.emails:
        profile.email = pii.emails[0]

    verification = verify_profile(profile)
    dimensions, total, engine = await score_candidate_async(
        profile, verification, criteria, job_title
    )
    strengths, weaknesses = compose_strengths_weaknesses(dimensions)
    questions = await generate_questions_async(
        dimensions,
        profile,
        criteria,
        verification,
        job_title=job_title,
        weaknesses=weaknesses,
    )

    return CandidateReport(
        profile=profile,
        verification=verification,
        dimensions=dimensions,
        total_score=total,
        strengths=strengths,
        weaknesses=weaknesses,
        interview_questions=questions,
        generated_at=datetime.now(timezone.utc).isoformat(),
        engine=engine,
    )


async def compute_report(
    session: AsyncSession, candidate: Candidate
) -> CandidateReport:
    """为单个候选人生成/刷新报告，写回 candidate.score & candidate.report。"""
    job = await session.get(Job, candidate.job_id)
    if job is None:
        raise ValueError("candidate.job_id 指向不存在的职位")

    criteria = JobCriteria.model_validate(job.criteria or {})
    text, _ = await _load_resume_text(session, candidate)
    report = await _build_report_async(text, criteria, job.title, candidate.name)

    candidate.report = report.model_dump(mode="json")
    candidate.score = report.total_score
    candidate.updated_at = datetime.now(timezone.utc)
    session.add(candidate)
    await session.commit()
    await session.refresh(candidate)
    return report


async def compute_reports_bulk(
    session: AsyncSession, candidate_ids: list[str]
) -> int:
    """批量评估。单个失败不中断整体，返回成功数量。"""
    ok = 0
    for cid in candidate_ids:
        candidate = await session.get(Candidate, cid)
        if candidate is None:
            continue
        try:
            await compute_report(session, candidate)
            ok += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception("compute_report failed for %s: %s", cid, exc)
    return ok
