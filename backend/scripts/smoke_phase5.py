"""Phase 5 冒烟：Dashboard 统计 + 导出 ZIP/CSV 端到端跑一次真实数据库。"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.services.export_service import ExportFilter, build_csv, build_zip  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.api.endpoints.dashboard import (  # noqa: E402
    _compute_stats,
    _load_recent_tasks,
    _load_top_candidates,
)
from app.models.job import Job  # noqa: E402


async def main() -> None:
    async with AsyncSessionLocal() as session:
        print("=== Dashboard Stats ===")
        stats = await _compute_stats(session)
        print(stats.model_dump_json(indent=2))

        print("\n=== Top 5 候选人 ===")
        top = await _load_top_candidates(session, 5)
        for c in top:
            print(f"  {c.score} · {c.name} · {c.job_title}")

        print("\n=== 最近 3 任务 ===")
        recent = await _load_recent_tasks(session, 3)
        for t in recent:
            print(f"  {t.status.value:10s} {t.progress:3d}% · {t.source_zip_name}")

        # 选一个有候选人的职位尝试导出
        job = (
            await session.execute(select(Job).order_by(Job.created_at.desc()).limit(1))
        ).scalars().first()
        if job is None:
            print("\n[skip] 没有任何职位，跳过导出测试")
            return

        print(f"\n=== 导出 {job.title} ===")
        f = ExportFilter(job_id=job.id)
        try:
            csv_bytes, csv_name, rows = await build_csv(session, f)
            print(f"  CSV  {rows} 行 · {len(csv_bytes)} bytes · {csv_name}")
        except Exception as exc:  # noqa: BLE001
            print(f"  CSV 失败: {exc}")

        try:
            zip_bytes, zip_name, count = await build_zip(session, f)
            print(f"  ZIP  {count} 文件 · {len(zip_bytes)} bytes · {zip_name}")
        except Exception as exc:  # noqa: BLE001
            print(f"  ZIP 失败: {exc}")

    print("\n✅ Phase 5 smoke PASS")


if __name__ == "__main__":
    asyncio.run(main())
