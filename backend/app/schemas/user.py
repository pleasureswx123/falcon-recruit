"""用户相关的 Pydantic Schema。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """用户注册请求。"""
    email: EmailStr
    password: str = Field(
        min_length=6,
        description="密码长度必须在 6-72 字节之间（UTF-8编码）",
    )
    full_name: Optional[str] = Field(None, max_length=100)


class UserLogin(BaseModel):
    """用户登录请求。"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """用户响应（不包含敏感信息）。"""
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
