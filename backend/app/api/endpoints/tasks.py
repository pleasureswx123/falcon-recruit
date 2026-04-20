"""分拣任务 API (TDD §4 · Phase 3)。

端点：
- POST   /api/tasks/upload          上传 ZIP，返回 task_id（异步执行分拣流水线）
- GET    /api/tasks/{task_id}       获取任务状态与进度
- GET    /api/tasks                 列表（支持 job_id 过滤）
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, SessionDep
from app.models.candidate import Candidate
from app.models.file import FileType, ParseStatus, ResumeFile
from app.models.job import Job
from app.models.task import SortingTask, TaskStatus
from app.schemas.task import TaskListResponse, TaskRead
from app.services.zip_processor import run_pipeline

router = APIRouter(tags=["tasks"])
logger = logging.getLogger(__name__)


async def _execute_pipeline(task_id: str, zip_bytes: bytes) -> None:
    """后台协程：独立 session 跑分拣流水线，异常全部回写任务记录。"""
    async with AsyncSessionLocal() as session:
        task = await session.get(SortingTask, task_id)
        if task is None:
            return
        job = await session.get(Job, task.job_id)
        if job is None:
            task.status = TaskStatus.FAILED
            task.error_message = "关联的职位已不存在"
            task.finished_at = datetime.now(timezone.utc)
            session.add(task)
            await session.commit()
            return
        try:
            await run_pipeline(session, task, job, zip_bytes)
        except Exception as exc:  # noqa: BLE001
            logger.exception("pipeline crashed task_id=%s", task_id)
            task.status = TaskStatus.FAILED
            task.error_message = f"{type(exc).__name__}: {exc}"
            task.updated_at = datetime.now(timezone.utc)
            task.finished_at = datetime.now(timezone.utc)
            session.add(task)
            await session.commit()


@router.post(
    "/upload",
    response_model=TaskRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="上传 ZIP 启动分拣任务",
)
async def upload_zip(
    session: SessionDep,
    job_id: str = Form(..., description="目标职位 ID"),
    file: UploadFile = File(..., description="简历 ZIP 压缩包"),
) -> TaskRead:
    settings = get_settings()
    # 1. 校验职位
    job = await session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="职位不存在")

    # 2. 读字节并校验大小
    data = await file.read()
    size_mb = len(data) / 1024 / 1024
    if size_mb > settings.max_upload_mb:
        raise HTTPException(
            status_code=413,
            detail=f"ZIP 超出限制 {settings.max_upload_mb} MB，实际 {size_mb:.1f} MB",
        )
    if not data:
        raise HTTPException(status_code=400, detail="文件为空")

    # 3. 校验后缀（非强制：只做友好提示）
    name_lower = (file.filename or "").lower()
    if not name_lower.endswith(".zip"):
        raise HTTPException(status_code=400, detail="仅支持 .zip 格式")

    # 4. 创建任务记录
    task = SortingTask(
        job_id=job_id,
        source_zip_name=file.filename or "uploaded.zip",
        source_zip_size=len(data),
        status=TaskStatus.PENDING,
        stage_message="已接收上传，排队中",
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # 5. 启动后台协程
    asyncio.create_task(_execute_pipeline(task.id, data))

    return TaskRead.model_validate(task)


@router.get("", response_model=TaskListResponse, summary="任务列表")
async def list_tasks(
    session: SessionDep,
    job_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> TaskListResponse:
    base = select(SortingTask)
    if job_id:
        base = base.where(SortingTask.job_id == job_id)
    total = (await session.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one()
    offset = (page - 1) * page_size
    rows_stmt = base.order_by(SortingTask.created_at.desc()).offset(offset).limit(page_size)
    rows = (await session.execute(rows_stmt)).scalars().all()
    return TaskListResponse(
        total=total,
        items=[TaskRead.model_validate(r) for r in rows],
    )


@router.get("/{task_id}", response_model=TaskRead, summary="任务详情")
async def get_task(task_id: str, session: SessionDep) -> TaskRead:
    task = await session.get(SortingTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskRead.model_validate(task)


class UnmatchedFileItem(BaseModel):
    file_id: str
    original_name: str
    file_type: FileType
    mime: str | None
    size: int
    parse_status: ParseStatus
    parse_error: str | None
    text_excerpt: str | None
    zip_member: str
    candidate_id: str | None
    reason: str


class UnmatchedFilesResponse(BaseModel):
    task_id: str
    job_id: str
    total: int
    items: list[UnmatchedFileItem]


@router.get(
    "/{task_id}/unmatched-files",
    response_model=UnmatchedFilesResponse,
    summary="列出任务中需要人工挂载的孤立文件（无 PII 的匿名候选人文件）",
)
async def list_unmatched_files(task_id: str, session: SessionDep) -> UnmatchedFilesResponse:
    task = await session.get(SortingTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 判定 "孤立文件"：
    # 1. candidate_id 为空；或
    # 2. 关联的候选人 name/phone/email/wechat 四项全空（匿名兜底 group）
    stmt = (
        select(ResumeFile, Candidate)
        .outerjoin(Candidate, ResumeFile.candidate_id == Candidate.id)
        .where(ResumeFile.task_id == task_id)
        .where(
            or_(
                ResumeFile.candidate_id.is_(None),
                (
                    Candidate.name.is_(None)
                    & Candidate.phone.is_(None)
                    & Candidate.email.is_(None)
                    & Candidate.wechat.is_(None)
                ),
            )
        )
        .order_by(ResumeFile.created_at.asc())
    )

    # 归一化 diagnostics 中已经有的 reason，便于返回
    diag_reasons: dict[str, str] = {}
    diag = task.diagnostics or {}
    for rec in diag.get("unmatched_files", []) or []:
        if rec.get("file_id"):
            diag_reasons[rec["file_id"]] = rec.get("reason") or ""

    items: list[UnmatchedFileItem] = []
    for row in (await session.execute(stmt)).all():
        f: ResumeFile = row[0]
        reason = diag_reasons.get(f.id) or (
            "未关联到任何候选人" if f.candidate_id is None else "匿名候选人（无 PII 信息）"
        )
        items.append(
            UnmatchedFileItem(
                file_id=f.id,
                original_name=f.original_name,
                file_type=f.file_type,
                mime=f.mime,
                size=f.size,
                parse_status=f.parse_status,
                parse_error=f.parse_error,
                text_excerpt=f.text_excerpt,
                zip_member=f.zip_member,
                candidate_id=f.candidate_id,
                reason=reason,
            )
        )

    return UnmatchedFilesResponse(
        task_id=task_id,
        job_id=task.job_id,
        total=len(items),
        items=items,
    )
