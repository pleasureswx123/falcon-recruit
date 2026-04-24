"""认证路由 - 用户注册、登录、登出。"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_session, delete_session, get_current_user
from app.core.config import get_settings
from app.core.database import get_session
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services import user_service

router = APIRouter(tags=["认证"])


def _get_cookie_secure_flag() -> bool:
    """根据环境变量决定 Cookie 是否启用 Secure 属性。
    
    - 生产环境（APP_ENV=production）：True（需要 HTTPS）
    - 开发/测试环境：False（允许 HTTP）
    """
    settings = get_settings()
    return settings.app_env == "production"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # 每分钟最多 5 次注册请求
async def register(
    request: Request,
    user_data: UserCreate,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    """用户注册。
    
    - 验证邮箱唯一性
    - 哈希密码并创建用户
    - 自动登录（创建 Session 并设置 Cookie）
    """
    try:
        user = await user_service.create_user(session, user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # 创建 Session
    session_id = await create_session(user.id)
    
    # 设置 HttpOnly Cookie（根据环境动态设置 Secure 属性）
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=_get_cookie_secure_flag(),  # 生产环境 True，开发环境 False
        samesite="lax",
        max_age=86400,  # 24小时
    )
    
    return user


@router.post("/login", response_model=UserResponse)
@limiter.limit("10/minute")  # 每分钟最多 10 次登录请求（防止暴力破解）
async def login(
    request: Request,
    login_data: UserLogin,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    """用户登录。
    
    - 验证邮箱和密码
    - 创建 Session 并设置 Cookie
    """
    user = await user_service.authenticate_user(
        session, login_data.email, login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Cookie"},
        )
    
    # 创建 Session
    session_id = await create_session(user.id)
    
    # 设置 HttpOnly Cookie（根据环境动态设置 Secure 属性）
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=_get_cookie_secure_flag(),  # 生产环境 True，开发环境 False
        samesite="lax",
        max_age=86400,  # 24小时
    )
    
    return user


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
):
    """用户登出。
    
    - 删除服务端 Session
    - 清除客户端 Cookie
    """
    # 从请求中获取 Session ID 并删除
    session_id = response.cookies.get("session_id")
    if session_id:
        await delete_session(session_id)
    
    # 清除 Cookie
    response.delete_cookie(key="session_id")
    
    return {"message": "已登出"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息。"""
    return current_user
