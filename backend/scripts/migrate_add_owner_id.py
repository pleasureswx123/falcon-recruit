"""为 jobs 表添加 owner_id 字段并迁移现有数据。

此脚本用于在部署多租户数据隔离功能前执行数据库迁移。
策略：
1. 如果数据库已有用户，使用第一个用户作为默认所有者
2. 如果没有用户，创建一个默认系统用户
3. 将所有现有 job 记录分配给该用户
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.auth import hash_password
from app.core.database import AsyncSessionLocal


async def migrate():
    """执行数据库迁移。"""
    print("=" * 60)
    print("开始执行数据隔离迁移：为 jobs 表添加 owner_id 字段")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. 添加 owner_id 列（允许 NULL，暂时不设置 NOT NULL）
            print("\n[1/5] 添加 owner_id 列...")
            await session.execute(text("""
                ALTER TABLE jobs ADD COLUMN IF NOT EXISTS owner_id INTEGER;
            """))
            await session.commit()
            print("✓ owner_id 列已添加")
            
            # 2. 查找或创建默认用户
            print("\n[2/5] 查找或创建默认系统用户...")
            result = await session.execute(text(
                "SELECT id, email FROM users ORDER BY id LIMIT 1"
            ))
            first_user = result.first()
            
            if first_user:
                default_user_id = first_user[0]
                default_user_email = first_user[1]
                print(f"✓ 找到现有用户: ID={default_user_id}, Email={default_user_email}")
            else:
                # 创建默认系统用户
                print("  数据库中无用户，创建默认系统用户...")
                default_email = "admin@falcon-recruit.local"
                default_password = "admin123456"  # 默认密码，首次登录后应修改
                
                insert_sql = text("""
                    INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at)
                    VALUES (
                        :email,
                        :hashed_password,
                        :full_name,
                        :is_active,
                        :is_superuser,
                        NOW(),
                        NOW()
                    )
                    RETURNING id
                """)
                
                result = await session.execute(
                    insert_sql,
                    {
                        "email": default_email,
                        "hashed_password": hash_password(default_password),
                        "full_name": "系统管理员",
                        "is_active": True,
                        "is_superuser": True,
                    }
                )
                default_user_id = result.scalar()
                await session.commit()
                
                print(f"✓ 已创建默认用户:")
                print(f"  - Email: {default_email}")
                print(f"  - Password: {default_password}")
                print(f"  - User ID: {default_user_id}")
                print(f"  ⚠️  请尽快登录并修改密码！")
            
            # 3. 为现有 job 记录设置 owner_id
            print("\n[3/5] 为现有职位数据设置归属...")
            result = await session.execute(text(
                "SELECT COUNT(*) FROM jobs WHERE owner_id IS NULL"
            ))
            jobs_without_owner = result.scalar()
            
            if jobs_without_owner > 0:
                await session.execute(text(f"""
                    UPDATE jobs SET owner_id = {default_user_id} WHERE owner_id IS NULL;
                """))
                await session.commit()
                print(f"✓ 已将 {jobs_without_owner} 个职位分配给用户 {default_user_id}")
            else:
                print("✓ 所有职位已有 owner_id，无需更新")
            
            # 4. 添加外键约束
            print("\n[4/5] 添加外键约束...")
            try:
                await session.execute(text("""
                    ALTER TABLE jobs ADD CONSTRAINT fk_jobs_owner 
                    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;
                """))
                await session.commit()
                print("✓ 外键约束已添加")
            except Exception as e:
                # PostgreSQL 中如果约束已存在会报错，这是正常的
                if "already exists" not in str(e).lower():
                    raise
                print("✓ 外键约束已存在，跳过")
            
            # 5. 设置 owner_id 为 NOT NULL
            print("\n[5/5] 设置 owner_id 为 NOT NULL...")
            try:
                await session.execute(text("""
                    ALTER TABLE jobs ALTER COLUMN owner_id SET NOT NULL;
                """))
                await session.commit()
                print("✓ owner_id 已设置为 NOT NULL")
            except Exception as e:
                # 如果已经设置了 NOT NULL，跳过
                if "not null" not in str(e).lower() or "already" in str(e).lower():
                    raise
                print("✓ owner_id 已经是 NOT NULL，跳过")
            
            # 6. 创建索引
            print("\n[6/6] 创建索引...")
            try:
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_jobs_owner_id ON jobs(owner_id);
                """))
                await session.commit()
                print("✓ 索引已创建")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    raise
                print("✓ 索引已存在，跳过")
            
            print("\n" + "=" * 60)
            print("✓ 迁移完成！")
            print("=" * 60)
            print("\n下一步：")
            print("1. 重启后端服务以加载新的数据模型")
            print("2. 使用默认用户登录（如果没有其他用户）")
            print("3. 验证数据隔离功能是否正常")
            
        except Exception as e:
            await session.rollback()
            print("\n" + "=" * 60)
            print(f"✗ 迁移失败: {e}")
            print("=" * 60)
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
