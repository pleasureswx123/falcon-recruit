"""用户服务层 - 处理用户相关的业务逻辑。"""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.auth import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


async def create_user(
    session: AsyncSession,
    user_data: UserCreate,
) -> User:
    """创建新用户，自动哈希密码。"""
    # 检查邮箱是否已存在
    result = await session.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise ValueError(f"邮箱 {user_data.email} 已被注册")
    
    # 创建用户
    hashed_pw = hash_password(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        full_name=user_data.full_name,
    )
    
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    
    return db_user


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> Optional[User]:
    """验证用户凭据，返回用户对象或 None。"""
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    if not user.is_active:
        return None
    
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """根据邮箱查询用户。"""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    """根据ID查询用户。"""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
