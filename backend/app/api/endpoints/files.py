"""文件 API (Phase 3)。

端点：
- GET /api/files/{file_id}/download       下载原始文件（强制附件）
- GET /api/files/{file_id}/preview        内联预览（PDF/图片）
"""
from __future__ import annotations

import os
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.database import SessionDep
from app.core.auth import get_current_user
from app.models.job import Job
from app.models.user import User
from app.services import candidate_service as cs

router = APIRouter(tags=["files"])


def _make_filename_header(name: str) -> str:
    """RFC 5987 兼容的 filename* 头，处理中文。"""
    ascii_fallback = name.encode("ascii", "ignore").decode() or "download"
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quote(name)}"


@router.get("/{file_id}/download", summary="下载文件（带重命名）")
async def download_file(
    file_id: str,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
    rename: bool = Query(default=True, description="是否使用 AI 生成的重命名"),
) -> FileResponse:
    # 验证文件归属
    file_record = await cs.get_file(session, file_id)
    if file_record is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    job = await session.get(Job, file_record.job_id)
    if not job or job.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该文件")
    
    if not os.path.exists(file_record.file_path):
        raise HTTPException(status_code=410, detail="物理文件已清理")
    display = (file_record.new_name if rename else None) or file_record.original_name or "file"
    return FileResponse(
        file_record.file_path,
        media_type=file_record.mime or "application/octet-stream",
        headers={"Content-Disposition": _make_filename_header(display)},
    )


@router.get("/{file_id}/preview", summary="内联预览（PDF/图片）")
async def preview_file(
    file_id: str,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    # 验证文件归属
    file_record = await cs.get_file(session, file_id)
    if file_record is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    job = await session.get(Job, file_record.job_id)
    if not job or job.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该文件")
    
    if not os.path.exists(file_record.file_path):
        raise HTTPException(status_code=410, detail="物理文件已清理")
    return FileResponse(
        file_record.file_path,
        media_type=file_record.mime or "application/octet-stream",
        headers={
            "Content-Disposition": (
                f"inline; filename*=UTF-8''{quote(file_record.original_name or 'file')}"
            )
        },
    )
