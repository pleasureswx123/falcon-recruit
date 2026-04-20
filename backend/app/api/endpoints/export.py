"""批量导出 API (TDD §4 · Phase 5)。

端点：
- GET /api/export/zip/{job_id}    打包该职位下（经过滤的）候选人所有重命名文件
- GET /api/export/csv/{job_id}    导出候选人评分 CSV (UTF-8 BOM，Excel 友好)
"""
from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response

from app.core.config import get_settings
from app.core.database import SessionDep
from app.core.rate_limit import limiter
from app.services import export_service as es
from app.services.export_service import ExportFilter

router = APIRouter(tags=["export"])


def _attachment_header(name: str) -> str:
    ascii_fallback = name.encode("ascii", "ignore").decode() or "download"
    return (
        f"attachment; filename=\"{ascii_fallback}\"; "
        f"filename*=UTF-8''{quote(name)}"
    )


@router.get("/zip/{job_id}", summary="批量导出重命名附件 ZIP")
@limiter.limit(lambda: get_settings().rate_limit_export)
async def export_zip(
    request: Request,
    job_id: str,
    session: SessionDep,
    verified_only: bool = Query(
        default=False, description="仅导出已人工核验的候选人"
    ),
    min_score: int | None = Query(
        default=None, ge=0, le=100, description="仅导出达到此分数的候选人"
    ),
) -> Response:
    try:
        data, filename, count = await es.build_zip(
            session,
            ExportFilter(
                job_id=job_id,
                verified_only=verified_only,
                min_score=min_score,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if count == 0:
        raise HTTPException(
            status_code=404, detail="当前筛选条件下没有可导出的文件"
        )

    return Response(
        content=data,
        media_type="application/zip",
        headers={
            "Content-Disposition": _attachment_header(filename),
            "X-File-Count": str(count),
        },
    )


@router.get("/csv/{job_id}", summary="导出候选人评分 CSV")
@limiter.limit(lambda: get_settings().rate_limit_export)
async def export_csv(
    request: Request,
    job_id: str,
    session: SessionDep,
    verified_only: bool = Query(default=False),
    min_score: int | None = Query(default=None, ge=0, le=100),
) -> Response:
    try:
        data, filename, count = await es.build_csv(
            session,
            ExportFilter(
                job_id=job_id,
                verified_only=verified_only,
                min_score=min_score,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return Response(
        content=data,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": _attachment_header(filename),
            "X-Row-Count": str(count),
        },
    )
