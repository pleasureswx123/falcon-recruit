"""Phase 3 分拣流水线端到端冒烟测试。

构造一个包含 3 位候选人素材的测试 ZIP：
    01_张三/  简历.pdf   作品集.pdf(无 PII，靠同目录聚类)
    02_李四/  简历.docx  作品.txt(含重复手机号，靠 PII 合并)
    lost/     孤立简历.pdf(PII 独立，应成为第 3 位候选人)

执行：
    cd backend
    ./.venv/Scripts/python.exe scripts/smoke_sorting.py
"""
from __future__ import annotations

import asyncio
import io
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./falcon_smoke_sort.db")
os.environ.setdefault("STORAGE_ROOT", "./storage_smoke")

# 清掉上一次的数据
smoke_db = ROOT / "falcon_smoke_sort.db"
if smoke_db.exists():
    smoke_db.unlink()


def build_pdf(text: str) -> bytes:
    """用 insert_htmlbox 生成包含中文文本层的 PDF（PyMuPDF 自带 CJK 字体回退）。"""
    import html

    import fitz
    doc = fitz.open()
    page = doc.new_page()
    body = html.escape(text).replace("\n", "<br/>")
    page.insert_htmlbox(
        fitz.Rect(50, 50, 550, 800),
        f'<div style="font-family: sans-serif; font-size: 11pt;">{body}</div>',
    )
    return doc.tobytes()


def build_docx(text: str) -> bytes:
    from docx import Document
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def build_zip() -> bytes:
    resume_zhang = (
        "个人简历\n姓名: 张三\n手机: 13800138000\n邮箱: zhangsan@example.com\n"
        "教育经历:\n2012-2016 清华大学 计算机\n"
        "工作经历:\n2016-2020 阿里巴巴 后端工程师\n项目经验: Java/Spring"
    )
    portfolio_zhang_noPII = (
        "本作品集展示近三年项目案例。\n项目一：分布式缓存中间件。\n"
        "采用 Redis 集群方案，QPS 提升 40%。"
    )
    resume_li = (
        "李四 个人简历\n姓名：李四\n手机号: 13987654321\n邮箱: lisi@demo.cn\n"
        "工作经验: 2018-2023 腾讯 前端开发\n技能: React/TypeScript"
    )
    portfolio_li_with_phone = (
        "李四补充材料\n微信: lisi_wx_2024\n联系电话 13987654321\n个人作品附件"
    )
    orphan_wang = (
        "王五个人简历\n姓名: 王五\n手机: 13612345678\n邮箱: wangwu@test.org\n"
        "求职意向: Python 工程师\n工作经历: 2015-至今 字节跳动"
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("01_zhangsan/简历.pdf", build_pdf(resume_zhang))
        zf.writestr("01_zhangsan/作品集.pdf", build_pdf(portfolio_zhang_noPII))
        zf.writestr("02_lisi/简历.docx", build_docx(resume_li))
        zf.writestr("02_lisi/补充材料.txt", portfolio_li_with_phone.encode("utf-8"))
        zf.writestr("lost/wangwu_cv.pdf", build_pdf(orphan_wang))
    return buf.getvalue()


async def main() -> None:
    from app.core.database import AsyncSessionLocal, init_db
    from app.models.candidate import Candidate
    from app.models.file import ResumeFile
    from app.models.job import Job, JobStatus
    from app.models.task import SortingTask
    from app.services.zip_processor import run_pipeline
    from sqlalchemy import select

    await init_db()

    async with AsyncSessionLocal() as session:
        job = Job(title="后端工程师", raw_jd="负责业务系统设计", criteria={}, status=JobStatus.ACTIVE)
        session.add(job)
        await session.commit()
        await session.refresh(job)

        task = SortingTask(job_id=job.id, source_zip_name="smoke.zip", source_zip_size=0)
        session.add(task)
        await session.commit()
        await session.refresh(task)

        zip_bytes = build_zip()
        task.source_zip_size = len(zip_bytes)
        session.add(task)
        await session.commit()

        print(f"[smoke] zip size = {len(zip_bytes)} bytes")
        result = await run_pipeline(session, task, job, zip_bytes)
        print(f"[smoke] pipeline: {result}")

        # 校验候选人
        cands = (await session.execute(
            select(Candidate).where(Candidate.job_id == job.id)
        )).scalars().all()
        print(f"[smoke] candidates = {len(cands)}")
        for c in cands:
            files = (await session.execute(
                select(ResumeFile).where(ResumeFile.candidate_id == c.id)
            )).scalars().all()
            print(f"  · {c.name!r} phone={c.phone} email={c.email} files={len(files)}")
            for f in files:
                print(f"      - [{f.file_type}] {f.original_name} -> {f.new_name}")

    assert len(cands) == 3, f"期望 3 位候选人，实际 {len(cands)}"
    print("\n[smoke] ✅ ALL PASS")


if __name__ == "__main__":
    asyncio.run(main())
