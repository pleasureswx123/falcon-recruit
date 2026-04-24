"""完整认证流程 smoke 测试。

前置：
- 启动后端服务
- 测试用户注册、登录、登出流程
- 验证 Session Cookie 设置
- 验证受保护接口的鉴权
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from app.core.database import init_db
from main import create_app


async def _main() -> None:
    await init_db()
    app = create_app()

    # 使用 TestClient 进行测试
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # 1. 测试用户注册
    print("[1/6] 测试用户注册...")
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "测试用户",
        },
    )
    assert register_response.status_code == 201, f"注册失败: {register_response.text}"
    user_data = register_response.json()
    assert user_data["email"] == "test@example.com"
    assert "session_id" in register_response.cookies
    print(f"✓ 注册成功，用户ID: {user_data['id']}")

    # 2. 测试重复注册（应该失败）
    print("[2/6] 测试重复注册...")
    duplicate_response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpass123",
        },
    )
    assert duplicate_response.status_code == 400
    print("✓ 重复注册被正确拒绝")

    # 3. 测试用户登录
    print("[3/6] 测试用户登录...")
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpass123",
        },
    )
    assert login_response.status_code == 200, f"登录失败: {login_response.text}"
    assert "session_id" in login_response.cookies
    session_cookie = login_response.cookies["session_id"]
    print(f"✓ 登录成功，Session ID: {session_cookie[:16]}...")

    # 4. 测试错误密码登录
    print("[4/6] 测试错误密码登录...")
    wrong_password_response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )
    assert wrong_password_response.status_code == 401
    print("✓ 错误密码被正确拒绝")

    # 5. 测试获取当前用户信息
    print("[5/6] 测试获取当前用户信息...")
    me_response = client.get(
        "/api/auth/me",
        cookies={"session_id": session_cookie},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == "test@example.com"
    print(f"✓ 获取用户信息成功: {me_data['full_name']}")

    # 6. 测试用户登出
    print("[6/6] 测试用户登出...")
    logout_response = client.post(
        "/api/auth/logout",
        cookies={"session_id": session_cookie},
    )
    assert logout_response.status_code == 200
    print("✓ 登出成功")

    # 7. 验证登出后 Session 失效
    print("[额外] 验证登出后 Session 失效...")
    me_after_logout = client.get(
        "/api/auth/me",
        cookies={"session_id": session_cookie},
    )
    assert me_after_logout.status_code == 401
    print("✓ 登出后 Session 已失效")

    print("\n✅ 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(_main())
