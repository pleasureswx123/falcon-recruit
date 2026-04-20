"""全局异常处理器。

功能：
- 捕获未处理的 Exception，返回统一的 JSON 错误体（含 request_id 便于排障）。
- 保留 FastAPI 自带 HTTPException 与 RequestValidationError 的行为，但改为统一字段名。
- 生产环境不把堆栈泄露给客户端，只写到后端日志。
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _err_body(code: str, message: str, request_id: str, extra: Any = None) -> dict:
    body = {"code": code, "message": message, "request_id": request_id}
    if extra is not None:
        body["detail"] = extra
    return body


def _rid(request: Request) -> str:
    # 优先尊重上游网关塞进来的 Trace ID，其次自行生成
    return (
        request.headers.get("x-request-id")
        or request.headers.get("x-trace-id")
        or uuid.uuid4().hex[:16]
    )


def register_exception_handlers(app: FastAPI) -> None:
    settings = get_settings()

    @app.exception_handler(HTTPException)
    async def _http_exc(request: Request, exc: HTTPException) -> JSONResponse:
        rid = _rid(request)
        logger.info(
            "http_error",
            extra={
                "request_id": rid,
                "path": request.url.path,
                "status": exc.status_code,
                "detail": str(exc.detail),
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_err_body(
                code=f"http_{exc.status_code}",
                message=str(exc.detail),
                request_id=rid,
            ),
            headers={"X-Request-ID": rid},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        rid = _rid(request)
        logger.info(
            "validation_error",
            extra={"request_id": rid, "path": request.url.path},
        )
        return JSONResponse(
            status_code=422,
            content=_err_body(
                code="validation_error",
                message="请求参数校验失败",
                request_id=rid,
                extra=exc.errors(),
            ),
            headers={"X-Request-ID": rid},
        )

    @app.exception_handler(Exception)
    async def _unhandled_exc(request: Request, exc: Exception) -> JSONResponse:
        rid = _rid(request)
        # 服务端完整堆栈落本地日志（不对客户端暴露）
        logger.exception(
            "unhandled_exception",
            extra={
                "request_id": rid,
                "path": request.url.path,
                "type": type(exc).__name__,
            },
        )
        message = "internal server error"
        extra = None
        if settings.debug:
            # 开发环境才把异常消息 / 类型回显，方便本地排查
            message = f"{type(exc).__name__}: {exc}"
        return JSONResponse(
            status_code=500,
            content=_err_body(
                code="internal_error",
                message=message,
                request_id=rid,
                extra=extra,
            ),
            headers={"X-Request-ID": rid},
        )
