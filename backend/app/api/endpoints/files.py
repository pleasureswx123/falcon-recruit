"""文件 API (Phase 3)。

端点：
- GET /api/files/{file_id}/download       下载原始文件（强制附件）
- GET /api/files/{file_id}/preview        内联预览（PDF/图片）
"""
from __future__ import annotations

import os
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.database import SessionDep
from app.services import candidate_service as cs

router = APIRouter(tags=["files"])


def _make_filename_header(name: str) -> str:
    """RFC 5987 兼容的 filename* 头，处理中文。"""
    ascii_fallback = name.encode("ascii", "ignore").decode() or "download"
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quote(name)}"


@router.get("/{file_id}/download", summary="下载文件（带重命名）")
async def download_file(
    file_id: str, session: SessionDep,
    rename: bool = Query(default=True, description="是否使用 AI 生成的重命名"),
) -> FileResponse:
    record = await cs.get_file(session, file_id)
    if record is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    if not os.path.exists(record.file_path):
        raise HTTPException(status_code=410, detail="物理文件已清理")
    display = (record.new_name if rename else None) or record.original_name or "file"
    return FileResponse(
        record.file_path,
        media_type=record.mime or "application/octet-stream",
        headers={"Content-Disposition": _make_filename_header(display)},
    )


@router.get("/{file_id}/preview", summary="内联预览（PDF/图片）")
async def preview_file(file_id: str, session: SessionDep) -> FileResponse:
    record = await cs.get_file(session, file_id)
    if record is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    if not os.path.exists(record.file_path):
        raise HTTPException(status_code=410, detail="物理文件已清理")
    return FileResponse(
        record.file_path,
        media_type=record.mime or "application/octet-stream",
        headers={
            "Content-Disposition": (
                f"inline; filename*=UTF-8''{quote(record.original_name or 'file')}"
            )
        },
    )
