"""导出服务 (TDD §4 · Phase 5)。

负责：
- 打包某职位下所有（或经过滤的）重命名文件为 ZIP
- 生成候选人评分 CSV（UTF-8 BOM，Excel 友好）
"""
from __future__ import annotations

import csv
import io
import logging
import os
import zipfile
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.file import ResumeFile
from app.models.job import Job

logger = logging.getLogger(__name__)

_DIM_HEADERS = [
    ("hard_requirements", "硬性条件"),
    ("professional_background", "专业背景"),
    ("stability", "稳定性"),
    ("soft_skills", "软技能"),
    ("expectation_fit", "期望契合度"),
]


@dataclass(slots=True)
class ExportFilter:
    job_id: str
    verified_only: bool = False
    min_score: int | None = None


async def _load_job(session: AsyncSession, job_id: str) -> Job | None:
    return await session.get(Job, job_id)


async def _load_candidates(
    session: AsyncSession, f: ExportFilter
) -> list[Candidate]:
    stmt = select(Candidate).where(Candidate.job_id == f.job_id)
    if f.verified_only:
        stmt = stmt.where(Candidate.is_verified.is_(True))
    if f.min_score is not None:
        stmt = stmt.where(Candidate.score.is_not(None)).where(
            Candidate.score >= f.min_score
        )
    stmt = stmt.order_by(
        Candidate.score.desc().nullslast(), Candidate.created_at.desc()
    )
    return list((await session.execute(stmt)).scalars().all())


async def _load_files_for(
    session: AsyncSession, candidate_ids: list[str]
) -> list[ResumeFile]:
    if not candidate_ids:
        return []
    stmt = (
        select(ResumeFile)
        .where(ResumeFile.candidate_id.in_(candidate_ids))
        .order_by(ResumeFile.file_type.asc(), ResumeFile.created_at.asc())
    )
    return list((await session.execute(stmt)).scalars().all())


def _safe_member_name(name: str, used: set[str]) -> str:
    """ZIP 内部条目名去重；保留中文。"""
    if name not in used:
        used.add(name)
        return name
    stem, ext = os.path.splitext(name)
    for i in range(2, 1000):
        alt = f"{stem}({i}){ext}"
        if alt not in used:
            used.add(alt)
            return alt
    used.add(name)
    return name


async def build_zip(
    session: AsyncSession, f: ExportFilter
) -> tuple[bytes, str, int]:
    """打包重命名文件为 ZIP。返回 (bytes, 建议文件名, 文件数)。"""
    job = await _load_job(session, f.job_id)
    if job is None:
        raise ValueError("职位不存在")

    candidates = await _load_candidates(session, f)
    files = await _load_files_for(session, [c.id for c in candidates])

    buf = io.BytesIO()
    used_names: set[str] = set()
    counted = 0

    with zipfile.ZipFile(
        buf, "w", zipfile.ZIP_DEFLATED, allowZip64=True
    ) as zf:
        for rec in files:
            if not rec.file_path or not os.path.exists(rec.file_path):
                continue
            display = rec.new_name or rec.original_name or rec.id
            arcname = _safe_member_name(display, used_names)
            try:
                zf.write(rec.file_path, arcname=arcname)
                counted += 1
            except OSError as exc:
                logger.warning("zip write failed %s: %s", rec.file_path, exc)

    ts = datetime.now().strftime("%Y%m%d-%H%M")
    filename = f"{job.title}-候选人附件-{ts}.zip"
    return buf.getvalue(), filename, counted


def _dim_score(report: dict, key: str) -> str:
    for d in report.get("dimensions", []) or []:
        if isinstance(d, dict) and d.get("dimension") == key:
            return str(d.get("score", ""))
    return ""


async def build_csv(
    session: AsyncSession, f: ExportFilter
) -> tuple[bytes, str, int]:
    """导出候选人评分表（UTF-8 BOM，Excel 友好）。"""
    job = await _load_job(session, f.job_id)
    if job is None:
        raise ValueError("职位不存在")

    candidates = await _load_candidates(session, f)

    buf = io.StringIO()
    writer = csv.writer(buf)
    header = [
        "姓名",
        "手机号",
        "邮箱",
        "微信",
        "总分",
        *[label for _, label in _DIM_HEADERS],
        "累计年限",
        "期望薪资",
        "期望地点",
        "履历断层(月)",
        "平均在职(月)",
        "是否核验",
        "优势",
        "不足",
        "更新时间",
    ]
    writer.writerow(header)

    for c in candidates:
        report = c.report or {}
        profile = report.get("profile") or {}
        verification = report.get("verification") or {}
        gaps = verification.get("gaps") or []
        real_gaps = [
            g for g in gaps if isinstance(g, dict) and not g.get("is_covered_by_education")
        ]
        gap_total = sum(int(g.get("months", 0)) for g in real_gaps)

        row = [
            c.name or "",
            c.phone or "",
            c.email or "",
            c.wechat or "",
            c.score if c.score is not None else "",
            *[_dim_score(report, key) for key, _ in _DIM_HEADERS],
            profile.get("total_years") or "",
            profile.get("expected_salary") or "",
            profile.get("expected_location") or profile.get("location") or "",
            gap_total if real_gaps else "",
            verification.get("average_tenure_months") or "",
            "是" if c.is_verified else "否",
            "；".join(report.get("strengths") or []),
            "；".join(report.get("weaknesses") or []),
            c.updated_at.strftime("%Y-%m-%d %H:%M"),
        ]
        writer.writerow(row)

    content = "\ufeff" + buf.getvalue()
    data = content.encode("utf-8")
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    filename = f"{job.title}-候选人评分-{ts}.csv"
    return data, filename, len(candidates)
