"""数据库诊断脚本：检查表结构和数据状态。"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def diagnose():
    """诊断数据库状态。"""
    print("=" * 60)
    print("数据库诊断报告")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. 检查 jobs 表结构
            print("\n[1] jobs 表结构:")
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'jobs' 
                ORDER BY ordinal_position
            """))
            for row in result:
                print(f"  - {row[0]}: {row[1]} (nullable={row[2]})")
            
            # 2. 检查 jobs 表数据量
            print("\n[2] jobs 表数据:")
            result = await session.execute(text("SELECT COUNT(*) FROM jobs"))
            total = result.scalar()
            print(f"  总计: {total} 条记录")
            
            if total > 0:
                result = await session.execute(text(
                    "SELECT id, title, owner_id FROM jobs LIMIT 5"
                ))
                print("  前 5 条:")
                for row in result:
                    print(f"    - ID={row[0]}, title={row[1]}, owner_id={row[2]}")
            
            # 3. 检查 users 表
            print("\n[3] users 表数据:")
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"  总计: {user_count} 个用户")
            
            if user_count > 0:
                result = await session.execute(text(
                    "SELECT id, email, is_active FROM users LIMIT 5"
                ))
                for row in result:
                    print(f"    - ID={row[0]}, email={row[1]}, active={row[2]}")
            
            # 4. 测试查询（模拟后端 list_jobs）
            print("\n[4] 测试查询（模拟后端 list_jobs）:")
            if user_count > 0:
                result = await session.execute(text("SELECT id FROM users ORDER BY id LIMIT 1"))
                first_user_id = result.scalar()
                
                try:
                    result = await session.execute(text(
                        f"SELECT COUNT(*) FROM jobs WHERE owner_id = {first_user_id}"
                    ))
                    job_count = result.scalar()
                    print(f"  ✓ 查询成功: 用户 {first_user_id} 有 {job_count} 个职位")
                except Exception as e:
                    print(f"  ✗ 查询失败: {e}")
            else:
                print("  跳过：没有用户")
            
            print("\n" + "=" * 60)
            print("诊断完成")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n✗ 诊断失败: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    asyncio.run(diagnose())
