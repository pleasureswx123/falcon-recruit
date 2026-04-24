"""快速检查数据库中的用户和职位数据"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.job import Job
from app.models.user import User


async def check():
    async with AsyncSessionLocal() as session:
        # 查询所有用户
        users = (await session.execute(select(User))).scalars().all()
        print("=" * 60)
        print("所有用户:")
        print("=" * 60)
        for u in users:
            print(f"  ID={u.id}, Email={u.email}")
        
        # 查询所有职位
        jobs = (await session.execute(select(Job))).scalars().all()
        print("\n" + "=" * 60)
        print("所有职位:")
        print("=" * 60)
        for j in jobs:
            print(f"  ID={j.id}")
            print(f"  Title={j.title}")
            print(f"  OwnerID={j.owner_id}")
            
            # 查找对应的用户
            owner = next((u for u in users if u.id == j.owner_id), None)
            if owner:
                print(f"  OwnerEmail={owner.email}")
            else:
                print(f"  OwnerEmail=UNKNOWN")
            print()


if __name__ == "__main__":
    asyncio.run(check())
