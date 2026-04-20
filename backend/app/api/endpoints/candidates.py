"""候选人 API (TDD §4 · Phase 3 + Phase 4)。

端点：
- GET    /api/candidates                    列表（按职位过滤）
- GET    /api/candidates/{id}               详情（含关联文件）
- GET    /api/candidates/{id}/report        AI 画像报告（五维评分 + 履历核验 + 面试建议）
- PATCH  /api/candidates/{id}               手动纠偏（姓名 / 电话 / 邮箱 / 验证标记）
- POST   /api/candidates/{id}/files/{fid}   把指定文件改挂到该候选人
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.database import SessionDep
from app.schemas.candidate import (
    CandidateDetail,
    CandidateFileRead,
    CandidateListResponse,
    CandidateRead,
    CandidateUpdate,
)
from app.schemas.profile import CandidateReport
from app.services import candidate_service as cs
from app.services import profile_pipeline as pp

router = APIRouter(tags=["candidates"])


@router.get("", response_model=CandidateListResponse, summary="候选人列表")
async def list_candidates(
    session: SessionDep,
    job_id: str | None = Query(default=None),
    keyword: str | None = Query(default=None, max_length=60),
    verified: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> CandidateListResponse:
    offset = (page - 1) * page_size
    total, rows = await cs.list_candidates(
        session,
        job_id=job_id,
        keyword=keyword,
        verified=verified,
        offset=offset,
        limit=page_size,
    )
    return CandidateListResponse(
        total=total,
        items=[CandidateRead.model_validate(r) for r in rows],
    )


@router.get("/{candidate_id}", response_model=CandidateDetail, summary="候选人详情")
async def get_candidate(candidate_id: str, session: SessionDep) -> CandidateDetail:
    candidate = await cs.get_candidate(session, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="候选人不存在")
    files = await cs.get_candidate_files(session, candidate_id)
    detail = CandidateDetail.model_validate(candidate)
    detail.files = [CandidateFileRead.model_validate(f) for f in files]
    return detail


@router.get(
    "/{candidate_id}/report",
    response_model=CandidateReport,
    summary="AI 画像报告（五维评分 + 核验 + 面试建议）",
)
async def get_candidate_report(
    candidate_id: str,
    session: SessionDep,
    refresh: bool = Query(default=False, description="强制重新计算"),
) -> CandidateReport:
    candidate = await cs.get_candidate(session, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="候选人不存在")
    if refresh or not candidate.report:
        return await pp.compute_report(session, candidate)
    return CandidateReport.model_validate(candidate.report)


@router.patch("/{candidate_id}", response_model=CandidateRead, summary="更新候选人")
async def update_candidate(
    candidate_id: str, payload: CandidateUpdate, session: SessionDep
) -> CandidateRead:
    candidate = await cs.get_candidate(session, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="候选人不存在")
    updated = await cs.update_candidate(session, candidate, payload)
    return CandidateRead.model_validate(updated)


@router.post(
    "/{candidate_id}/files/{file_id}",
    response_model=CandidateFileRead,
    summary="将文件改挂到该候选人",
)
async def reassign_file(
    candidate_id: str, file_id: str, session: SessionDep
) -> CandidateFileRead:
    candidate = await cs.get_candidate(session, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="候选人不存在")
    file = await cs.get_file(session, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    try:
        updated = await cs.reassign_file(session, file, candidate)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CandidateFileRead.model_validate(updated)
