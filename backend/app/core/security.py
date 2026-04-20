"""API Key 鉴权。

设计取舍：
- 默认情况（FALCON_API_KEY 未设置）保持"开放"语义，不破坏本地 smoke / 开发体验。
- 一旦设置了 FALCON_API_KEY，所有挂接 require_api_key 的路由必须带 X-API-Key 头。
- 健康检查 /api/health 与 /api/health/ready 无鉴权，便于容器 healthcheck / 监控探活。
"""
from __future__ import annotations

import secrets

from fastapi import Depends, Header, HTTPException, status

from app.core.config import get_settings


async def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """FastAPI 依赖：校验请求头中的 API Key。"""
    expected = get_settings().falcon_api_key
    if not expected:
        # 未配置则视为"开放模式"，仅打印一次性提示由调用方处理
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing X-API-Key",
        )


# 便捷别名：可直接用在路由依赖上
ApiKeyDep = Depends(require_api_key)
