"""per-IP 限流（slowapi）。

对外暴露 `limiter` 与 `attach_rate_limiter(app)`：
- 路由处通过 `@limiter.limit(settings.rate_limit_upload)` 声明速率；
- 被限流时自动返回 429，并带 Retry-After 头。
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

# 注意：slowapi.Limiter 默认会用系统 locale 读取 `.env`；中文 Windows 是 GBK，
# 会把 UTF-8 写的 .env 解码失败。这里显式指向一个绝对不存在的文件，跳过 env 读取。
# 所有配置走我们自己的 Settings（pydantic-settings 已显式指定 UTF-8）。
limiter = Limiter(
    key_func=get_remote_address,
    headers_enabled=True,
    config_filename=".env.slowapi-disabled",
)


async def _rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "code": "rate_limited",
            "message": f"请求过于频繁，{exc.detail}",
        },
        headers={"Retry-After": "60"},
    )


def attach_rate_limiter(app: FastAPI) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
