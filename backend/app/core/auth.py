"""认证工具 - 密码哈希、Session 管理。

设计取舍：
- 使用 bcrypt 直接进行密码哈希（不使用 passlib）
- Session 存储在 Redis（开发和生产环境统一）
- Cookie 设置为 HttpOnly + Secure（根据环境变量）+ SameSite=lax
"""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import redis.asyncio as redis
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.models.user import User

# Redis 客户端（懒加载）
_redis_client: Optional[redis.Redis] = None


def _get_redis_client() -> redis.Redis:
    """获取 Redis 客户端（单例）。"""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        redis_url = getattr(settings, "redis_url", None)
        if not redis_url:
            raise RuntimeError(
                "REDIS_URL not configured. Please set redis_url in .env or environment variables."
            )
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client


def hash_password(password: str) -> str:
    """哈希密码。
    
    注意：bcrypt 有 72 字节的限制，超过会被截断。
    这里我们主动检查并给出友好提示。
    """
    # bcrypt 最大支持 72 字节（不是字符）
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        raise ValueError("密码长度不能超过 72 字节（UTF-8 编码），当前密码为 {} 字节".format(len(password_bytes)))
    
    # 使用 bcrypt 直接哈希
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码。"""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


async def create_session(user_id: int) -> str:
    """创建 Session，返回 Session ID。"""
    session_id = secrets.token_urlsafe(32)
    
    # 存储到 Redis
    redis_client = _get_redis_client()
    session_data = {
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    # 设置过期时间（24小时）
    expire_seconds = 24 * 3600
    await redis_client.setex(
        f"session:{session_id}",
        expire_seconds,
        json.dumps(session_data),
    )
    
    return session_id


async def get_session_user_id(session_id: str) -> Optional[int]:
    """从 Session ID 获取用户 ID。"""
    redis_client = _get_redis_client()
    session_data_str = await redis_client.get(f"session:{session_id}")
    
    if not session_data_str:
        return None
    
    # Redis 已自动处理过期，直接解析数据
    session_data = json.loads(session_data_str)
    return session_data.get("user_id")


async def delete_session(session_id: str) -> None:
    """删除 Session。"""
    redis_client = _get_redis_client()
    await redis_client.delete(f"session:{session_id}")


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User:
    """从 Cookie 中读取 Session ID，验证并返回当前用户。"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录",
            headers={"WWW-Authenticate": "Cookie"},
        )
    
    # 从 Session 存储中获取用户ID
    user_id = await get_session_user_id(session_id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session 已过期，请重新登录",
        )
    
    # 查询用户
    from sqlmodel import select
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
        )
    
    return user


# 便捷别名：可直接用在路由依赖上
AuthDep = Depends(get_current_user)
