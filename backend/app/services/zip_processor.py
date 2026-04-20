"""ZIP 分拣流水线 (PRD 3.2 · TDD 3.1)。

全流程：
    解压（不信任文件名） → 逐文件解析文本 → 提取 PII
        → PII-Linker 合并 → 写入 Candidate / ResumeFile
        → 物理重命名到 storage/jobs/<job_id>/renamed/
"""
from __future__ import annotations

import asyncio
import io
import logging
import mimetypes
import os
import shutil
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.candidate import Candidate
from app.models.file import FileType, ParseStatus, ResumeFile
from app.models.job import Job
from app.models.task import SortingTask, TaskStatus
from app.services import file_parser as fp
from app.services.pii_extractor import extract_pii
from app.services.pii_linker import CandidateGroup, ParsedDoc, link

logger = logging.getLogger(__name__)

# 简历识别启发式关键词：命中任意一条即视为 RESUME
_RESUME_HINTS = (
    "工作经历", "工作经验", "教育经历", "教育背景", "求职意向",
    "个人简介", "自我评价", "项目经验", "项目经历", "个人技能",
    "简历", "Resume", "resume", "RESUME",
)

_EXT_BY_MIME = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "text/plain": ".txt",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


@dataclass(slots=True)
class PipelineResult:
    total_files: int
    parsed_files: int
    failed_files: int
    candidate_count: int


def _storage_dirs(job_id: str, task_id: str) -> tuple[Path, Path]:
    root = Path(get_settings().storage_root).resolve()
    raw = root / "jobs" / job_id / "tasks" / task_id / "raw"
    renamed = root / "jobs" / job_id / "renamed"
    raw.mkdir(parents=True, exist_ok=True)
    renamed.mkdir(parents=True, exist_ok=True)
    return raw, renamed


def _decode_zip_member_name(info: zipfile.ZipInfo) -> str:
    """ZIP 成员名的中文修正。GBK 回退解码，供 original_name 展示。"""
    if info.flag_bits & 0x800:  # UTF-8 标记
        return info.filename
    try:
        raw = info.filename.encode("cp437")
    except UnicodeEncodeError:
        return info.filename
    for enc in ("utf-8", "gbk", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return info.filename


def _pick_ext(mime: str, fallback: str) -> str:
    ext = _EXT_BY_MIME.get(mime)
    if ext:
        return ext
    guessed = mimetypes.guess_extension(mime or "")
    if guessed:
        return guessed
    return os.path.splitext(fallback)[1] or ".bin"


def _infer_file_type(mime: str, text: str) -> FileType:
    if not mime or mime == "unknown":
        return FileType.UNKNOWN
    if mime.startswith("image/"):
        return FileType.PORTFOLIO
    if any(h in text for h in _RESUME_HINTS):
        return FileType.RESUME
    # PDF/DOCX 但没命中简历关键词 → 作品集或其他
    return FileType.PORTFOLIO


def _safe_filename_part(value: str, fallback: str) -> str:
    cleaned = "".join(c for c in (value or "") if c not in '<>:"/\\|?*').strip()
    return cleaned or fallback


def _compose_new_name(name: str | None, job_title: str, ftype: FileType, ext: str) -> str:
    name_part = _safe_filename_part(name or "", "匿名")
    job_part = _safe_filename_part(job_title, "岗位")[:20]
    type_label = {
        FileType.RESUME: "简历",
        FileType.PORTFOLIO: "作品集",
        FileType.UNKNOWN: "附件",
    }[ftype]
    return f"[{name_part}-{job_part}-{type_label}]{ext}"


async def _update_task(
    session: AsyncSession,
    task: SortingTask,
    **kwargs,
) -> None:
    for k, v in kwargs.items():
        setattr(task, k, v)
    task.updated_at = datetime.now(timezone.utc)
    session.add(task)
    await session.commit()
    await session.refresh(task)


async def run_pipeline(
    session: AsyncSession,
    task: SortingTask,
    job: Job,
    zip_bytes: bytes,
) -> PipelineResult:
    """对单个 ZIP 执行完整分拣流水线。"""
    raw_dir, renamed_dir = _storage_dirs(job.id, task.id)

    # ---- 阶段 1：解压 ----
    await _update_task(
        session, task,
        status=TaskStatus.EXTRACTING,
        stage_message="正在解压 ZIP",
        progress=5,
    )

    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        await _update_task(
            session, task,
            status=TaskStatus.FAILED,
            stage_message="ZIP 损坏",
            error_message=str(exc),
            finished_at=datetime.now(timezone.utc),
        )
        return PipelineResult(0, 0, 0, 0)

    members = [m for m in zf.infolist() if not m.is_dir() and m.file_size > 0]
    total = len(members)
    await _update_task(
        session, task,
        total_files=total,
        stage_message=f"解压完成，共 {total} 个文件",
        progress=10,
    )

    # ---- 阶段 2：逐文件解析 + 提取 PII ----
    await _update_task(
        session, task, status=TaskStatus.PARSING,
        stage_message="正在解析文件并提取 PII",
    )
    docs: list[ParsedDoc] = []
    file_records: dict[str, ResumeFile] = {}
    parsed_ok = 0
    failed = 0

    for idx, info in enumerate(members, start=1):
        display_name = _decode_zip_member_name(info)
        try:
            data = zf.read(info)
        except Exception as exc:  # noqa: BLE001
            logger.warning("read zip member failed: %s -> %s", display_name, exc)
            failed += 1
            continue

        result = await asyncio.to_thread(fp.parse_file, data, display_name)
        ext = _pick_ext(result.mime, display_name)
        file_id = str(uuid.uuid4())
        raw_path = raw_dir / f"{file_id}{ext}"
        raw_path.write_bytes(data)

        ftype = _infer_file_type(result.mime, result.text)
        excerpt = result.text[:2000] if result.text else None

        record = ResumeFile(
            id=file_id,
            task_id=task.id,
            job_id=job.id,
            file_type=ftype,
            original_name=display_name,
            file_path=str(raw_path),
            mime=result.mime,
            size=len(data),
            parse_status=result.status,
            parse_error=result.error,
            text_excerpt=excerpt,
            zip_member=info.filename,
        )
        session.add(record)
        file_records[file_id] = record

        if result.status == ParseStatus.PARSED:
            parsed_ok += 1
            pii = extract_pii(result.text)
            docs.append(ParsedDoc(
                file_id=file_id,
                zip_member=info.filename,
                file_type=ftype,
                pii=pii,
                text_len=len(result.text),
            ))
        else:
            failed += 1

        # 每 3 个文件刷一次进度，减少写 DB 压力
        if idx % 3 == 0 or idx == total:
            percent = 10 + int(60 * idx / max(total, 1))
            await _update_task(
                session, task,
                parsed_files=parsed_ok, failed_files=failed,
                stage_message=f"解析中 {idx}/{total}",
                progress=percent,
            )

    await session.commit()  # flush file_records

    # ---- 阶段 3：PII 关联 ----
    await _update_task(
        session, task, status=TaskStatus.LINKING,
        stage_message="关联简历与作品集", progress=75,
    )
    groups = link(docs)

    diagnostics = await _persist_candidates(
        session, task, job, groups, file_records, renamed_dir
    )

    # ---- 阶段 3.5：AI 画像评分（Phase 4） ----
    await _update_task(
        session, task,
        stage_message="生成 AI 画像评分", progress=88,
    )
    try:
        from app.services.profile_pipeline import compute_reports_bulk

        candidate_ids = [c["candidate_id"] for c in diagnostics["candidates"]]
        await compute_reports_bulk(session, candidate_ids)
    except Exception as exc:  # noqa: BLE001
        logger.exception("scoring pipeline failed: %s", exc)

    # ---- 阶段 4：收尾 ----
    await _update_task(
        session, task,
        status=TaskStatus.SUCCEEDED,
        stage_message=f"完成，{len(groups)} 位候选人",
        progress=100,
        parsed_files=parsed_ok,
        failed_files=failed,
        candidate_count=len(groups),
        diagnostics=diagnostics,
        finished_at=datetime.now(timezone.utc),
    )
    return PipelineResult(total, parsed_ok, failed, len(groups))


async def _persist_candidates(
    session: AsyncSession,
    task: SortingTask,
    job: Job,
    groups: list[CandidateGroup],
    file_records: dict[str, ResumeFile],
    renamed_dir: Path,
) -> dict:
    """根据分组结果创建 Candidate，更新文件的 candidate_id / new_name，物理重命名。"""
    diagnostics: dict = {"candidates": [], "unmatched_files": []}

    for group in groups:
        candidate = Candidate(
            job_id=job.id,
            name=group.name,
            phone=group.phone,
            email=group.email,
            wechat=group.wechat,
            report={},
        )
        session.add(candidate)
        await session.flush()  # 获取 candidate.id 但不提交

        group_files = [file_records[fid] for fid in group.file_ids if fid in file_records]
        # 每个候选人组内：挑一份作为"简历"（文本最长的 RESUME；否则第一份）
        resumes = [f for f in group_files if f.file_type == FileType.RESUME]
        primary = resumes[0] if resumes else (group_files[0] if group_files else None)

        for f in group_files:
            f.candidate_id = candidate.id
            ext = os.path.splitext(f.file_path)[1]
            f.new_name = _compose_new_name(group.name, job.title, f.file_type, ext)
            # 物理复制到重命名目录；冲突时追加后缀
            target = renamed_dir / f.new_name
            if target.exists():
                stem = target.stem
                target = renamed_dir / f"{stem}-{f.id[:6]}{target.suffix}"
                f.new_name = target.name
            try:
                shutil.copy2(f.file_path, target)
            except OSError as exc:
                logger.warning("copy to renamed failed: %s", exc)
            session.add(f)

        diagnostics["candidates"].append({
            "candidate_id": candidate.id,
            "name": group.name,
            "phone": group.phone,
            "email": group.email,
            "file_ids": [f.id for f in group_files],
            "primary_file_id": primary.id if primary else None,
            "reason": group.reason,
        })

    # 完全未挂到任何 group 的文件（理论上不会发生，留兜底）
    linked = {fid for g in groups for fid in g.file_ids}
    for fid, rec in file_records.items():
        if fid not in linked:
            diagnostics["unmatched_files"].append({
                "file_id": fid,
                "original_name": rec.original_name,
                "reason": rec.parse_error or "未提取到 PII 且无同目录候选人",
            })

    # 匿名候选人（无姓名 & 无 PII）归入 unmatched：这些文件需要人工挂载
    for g in groups:
        if g.name or g.phone or g.email or g.wechat:
            continue
        for fid in g.file_ids:
            rec = file_records.get(fid)
            if rec is None:
                continue
            diagnostics["unmatched_files"].append({
                "file_id": fid,
                "original_name": rec.original_name,
                "reason": "未提取到 PII 且未命中目录/文件名聚类",
            })

    await session.commit()
    return diagnostics
