"""职位管理 API (TDD §4 · Phase 2)。

端点：
- POST   /api/jobs              创建职位，若未提供 criteria 自动解析生成
- GET    /api/jobs              列表，支持分页 / 状态过滤 / 关键词搜索
- GET    /api/jobs/{id}         详情
- PATCH  /api/jobs/{id}         局部更新
- DELETE /api/jobs/{id}         删除
- POST   /api/jobs/parse-jd     仅解析 JD 文本返回 criteria(不落库)，供前端预览
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.database import SessionDep
from app.models.job import JobStatus
from app.schemas.job import (
    JobCreate,
    JobCriteria,
    JobListResponse,
    JobRead,
    JobUpdate,
)
from app.services import job_service
from app.services.jd_parser import generate_jd_async, parse_jd_to_criteria_async

router = APIRouter(tags=["jobs"])


class ParseJdRequest(BaseModel):
    raw_jd: str = Field(min_length=1, description="待解析的 JD 文本")


class ParseJdResponse(BaseModel):
    criteria: JobCriteria


class GenerateJdRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120, description="职位名称")
    description: str = Field(min_length=5, max_length=500, description="岗位简单描述")


class GenerateJdResponse(BaseModel):
    jd_text: str


@router.post(
    "",
    response_model=JobRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建职位",
)
async def create_job(payload: JobCreate, session: SessionDep) -> JobRead:
    job = await job_service.create_job(session, payload)
    return JobRead.model_validate(job)


@router.get("", response_model=JobListResponse, summary="职位列表")
async def list_jobs(
    session: SessionDep,
    status_: JobStatus | None = Query(default=None, alias="status"),
    keyword: str | None = Query(default=None, max_length=60),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> JobListResponse:
    offset = (page - 1) * page_size
    total, rows = await job_service.list_jobs(
        session,
        status=status_,
        keyword=keyword,
        offset=offset,
        limit=page_size,
    )
    return JobListResponse(
        total=total,
        items=[JobRead.model_validate(r) for r in rows],
    )


@router.post(
    "/parse-jd",
    response_model=ParseJdResponse,
    summary="解析 JD 生成 criteria（不落库，供前端预览）",
)
async def parse_jd(payload: ParseJdRequest) -> ParseJdResponse:
    criteria = await parse_jd_to_criteria_async(payload.raw_jd)
    return ParseJdResponse(criteria=criteria)


@router.post(
    "/generate-jd",
    response_model=GenerateJdResponse,
    summary="AI 生成 JD 文本（不落库，供 HR 参考编辑后发布）",
)
async def generate_jd(payload: GenerateJdRequest) -> GenerateJdResponse:
    try:
        jd_text = await generate_jd_async(payload.title, payload.description)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return GenerateJdResponse(jd_text=jd_text)


@router.get("/{job_id}", response_model=JobRead, summary="职位详情")
async def get_job(job_id: str, session: SessionDep) -> JobRead:
    job = await job_service.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="职位不存在")
    return JobRead.model_validate(job)


@router.patch("/{job_id}", response_model=JobRead, summary="更新职位")
async def update_job(
    job_id: str, payload: JobUpdate, session: SessionDep
) -> JobRead:
    job = await job_service.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="职位不存在")
    updated = await job_service.update_job(session, job, payload)
    return JobRead.model_validate(updated)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除职位",
)
async def delete_job(job_id: str, session: SessionDep):
    job = await job_service.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="职位不存在")
    await job_service.delete_job(session, job)
    return None
