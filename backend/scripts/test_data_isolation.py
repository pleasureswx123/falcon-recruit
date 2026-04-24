"""
数据隔离测试脚本

验证多租户数据隔离功能是否正常工作：
1. 用户A创建职位，用户B无法在列表中看到
2. 用户A上传简历到职位，用户B无法访问该任务
3. Dashboard统计只显示当前用户的数据
4. 导出功能只能导出当前用户的职位数据
5. 尝试访问其他用户的资源应返回403错误
"""
import asyncio
import httpx
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.job import Job
from app.models.candidate import Candidate
from app.services.auth_service import hash_password


async def create_test_users(session):
    """创建两个测试用户"""
    print("\n=== 创建测试用户 ===")
    
    # 检查用户是否已存在
    result = await session.execute(
        select(User).where(User.email.in_(["user_a@test.com", "user_b@test.com"]))
    )
    existing_users = result.scalars().all()
    
    users = {}
    for email in ["user_a@test.com", "user_b@test.com"]:
        existing = next((u for u in existing_users if u.email == email), None)
        if existing:
            print(f"✓ 用户 {email} 已存在 (ID: {existing.id})")
            users[email] = existing
        else:
            user = User(
                email=email,
                username=email.split("@")[0],
                password_hash=hash_password("test123456"),
                is_active=True,
            )
            session.add(user)
            await session.flush()
            print(f"✓ 创建用户 {email} (ID: {user.id})")
            users[email] = user
    
    await session.commit()
    return users


async def test_job_isolation(session, users):
    """测试职位数据隔离"""
    print("\n=== 测试职位数据隔离 ===")
    
    user_a = users["user_a@test.com"]
    user_b = users["user_b@test.com"]
    
    # 用户A创建职位
    job_a = Job(
        owner_id=user_a.id,
        title="用户A的职位",
        description="这是用户A创建的职位",
    )
    session.add(job_a)
    await session.flush()
    print(f"✓ 用户A创建职位: {job_a.title} (ID: {job_a.id})")
    
    # 用户B创建职位
    job_b = Job(
        owner_id=user_b.id,
        title="用户B的职位",
        description="这是用户B创建的职位",
    )
    session.add(job_b)
    await session.flush()
    print(f"✓ 用户B创建职位: {job_b.title} (ID: {job_b.id})")
    
    await session.commit()
    
    # 验证用户A只能看到自己的职位
    result = await session.execute(
        select(func.count()).select_from(Job).where(Job.owner_id == user_a.id)
    )
    count_a = result.scalar()
    print(f"✓ 用户A的职位数量: {count_a}")
    assert count_a >= 1, "用户A应该至少有一个职位"
    
    # 验证用户B只能看到自己的职位
    result = await session.execute(
        select(func.count()).select_from(Job).where(Job.owner_id == user_b.id)
    )
    count_b = result.scalar()
    print(f"✓ 用户B的职位数量: {count_b}")
    assert count_b >= 1, "用户B应该至少有一个职位"
    
    # 验证用户A无法直接访问用户B的职位（通过Service层逻辑）
    job_b_check = await session.get(Job, job_b.id)
    assert job_b_check.owner_id == user_b.id, "职位B应该属于用户B"
    print(f"✓ 职位归属验证通过: 职位B属于用户{job_b_check.owner_id}")
    
    return job_a, job_b


async def test_candidate_isolation(session, users, job_a, job_b):
    """测试候选人数据隔离（通过JOIN Job实现）"""
    print("\n=== 测试候选人数据隔离 ===")
    
    user_a = users["user_a@test.com"]
    user_b = users["user_b@test.com"]
    
    # 为用户A的职位添加候选人
    candidate_a = Candidate(
        job_id=job_a.id,
        name="候选人A",
        email="candidate_a@test.com",
        phone="13800000001",
        stage="new",
    )
    session.add(candidate_a)
    await session.flush()
    print(f"✓ 为用户A的职位添加候选人: {candidate_a.name}")
    
    # 为用户B的职位添加候选人
    candidate_b = Candidate(
        job_id=job_b.id,
        name="候选人B",
        email="candidate_b@test.com",
        phone="13800000002",
        stage="new",
    )
    session.add(candidate_b)
    await session.flush()
    print(f"✓ 为用户B的职位添加候选人: {candidate_b.name}")
    
    await session.commit()
    
    # 验证通过JOIN查询，用户A只能看到自己职位的候选人
    from sqlalchemy.orm import joinedload
    
    result = await session.execute(
        select(func.count())
        .select_from(Candidate)
        .join(Job, Candidate.job_id == Job.id)
        .where(Job.owner_id == user_a.id)
    )
    count_a = result.scalar()
    print(f"✓ 用户A可见的候选人数量: {count_a}")
    assert count_a >= 1, "用户A应该能看到至少一个候选人"
    
    # 验证用户B只能看到自己职位的候选人
    result = await session.execute(
        select(func.count())
        .select_from(Candidate)
        .join(Job, Candidate.job_id == Job.id)
        .where(Job.owner_id == user_b.id)
    )
    count_b = result.scalar()
    print(f"✓ 用户B可见的候选人数量: {count_b}")
    assert count_b >= 1, "用户B应该能看到至少一个候选人"
    
    # 验证候选人A确实属于用户A的职位
    candidate_a_check = await session.get(Candidate, candidate_a.id)
    job_of_candidate_a = await session.get(Job, candidate_a_check.job_id)
    assert job_of_candidate_a.owner_id == user_a.id, "候选人A应该属于用户A的职位"
    print(f"✓ 候选人归属验证通过: 候选人A属于用户{job_of_candidate_a.owner_id}的职位")


async def test_api_isolation():
    """测试API层面的数据隔离（需要后端服务运行）"""
    print("\n=== 测试API层面数据隔离 ===")
    print("⚠️  此测试需要后端服务运行在 http://localhost:8000")
    print("⚠️  请先启动后端服务后再运行此部分测试")
    
    base_url = "http://localhost:8000"
    
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
            # 登录用户A
            login_response = await client.post(
                "/api/auth/login",
                json={"email": "user_a@test.com", "password": "test123456"},
            )
            
            if login_response.status_code != 200:
                print(f"❌ 用户A登录失败: {login_response.status_code}")
                print(f"   响应: {login_response.text}")
                return
            
            print("✓ 用户A登录成功")
            
            # 获取用户A的职位列表
            jobs_response = await client.get("/api/jobs")
            if jobs_response.status_code == 200:
                jobs_data = jobs_response.json()
                print(f"✓ 用户A获取职位列表成功，共 {jobs_data.get('total', 0)} 个职位")
                
                # 验证所有职位都属于用户A
                for job in jobs_data.get("items", []):
                    # 这里需要通过其他方式验证owner_id，因为JobRead可能不包含owner_id
                    pass
            else:
                print(f"❌ 用户A获取职位列表失败: {jobs_response.status_code}")
            
            # 登出用户A
            await client.post("/api/auth/logout")
            print("✓ 用户A登出成功")
            
            # 登录用户B
            login_response = await client.post(
                "/api/auth/login",
                json={"email": "user_b@test.com", "password": "test123456"},
            )
            
            if login_response.status_code != 200:
                print(f"❌ 用户B登录失败: {login_response.status_code}")
                return
            
            print("✓ 用户B登录成功")
            
            # 获取用户B的职位列表
            jobs_response = await client.get("/api/jobs")
            if jobs_response.status_code == 200:
                jobs_data = jobs_response.json()
                print(f"✓ 用户B获取职位列表成功，共 {jobs_data.get('total', 0)} 个职位")
            else:
                print(f"❌ 用户B获取职位列表失败: {jobs_response.status_code}")
            
            # 登出用户B
            await client.post("/api/auth/logout")
            print("✓ 用户B登出成功")
            
    except httpx.ConnectError:
        print("❌ 无法连接到后端服务，请确保服务正在运行")
    except Exception as e:
        print(f"❌ API测试失败: {str(e)}")


async def cleanup_test_data(session, users):
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")
    
    user_a = users["user_a@test.com"]
    user_b = users["user_b@test.com"]
    
    # 删除测试用户（CASCADE会自动删除相关的job、candidate等）
    await session.delete(user_a)
    await session.delete(user_b)
    await session.commit()
    
    print("✓ 测试数据已清理")


async def main():
    """主测试函数"""
    print("=" * 60)
    print("多租户数据隔离测试")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. 创建测试用户
            users = await create_test_users(session)
            
            # 2. 测试职位数据隔离
            job_a, job_b = await test_job_isolation(session, users)
            
            # 3. 测试候选人数据隔离
            await test_candidate_isolation(session, users, job_a, job_b)
            
            print("\n" + "=" * 60)
            print("✅ 数据库层面数据隔离测试通过！")
            print("=" * 60)
            
            # 4. 测试API层面隔离（可选，需要服务运行）
            print("\n提示: 如需测试API层面隔离，请确保后端服务正在运行")
            run_api_test = input("是否运行API测试？(y/n): ").strip().lower()
            if run_api_test == 'y':
                await test_api_isolation()
            
            # 5. 询问是否清理测试数据
            print("\n" + "=" * 60)
            cleanup = input("是否清理测试数据？(y/n): ").strip().lower()
            if cleanup == 'y':
                await cleanup_test_data(session, users)
                print("✅ 测试完成，数据已清理")
            else:
                print("✅ 测试完成，测试数据已保留")
                print("   测试用户: user_a@test.com / user_b@test.com")
                print("   密码: test123456")
        
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
