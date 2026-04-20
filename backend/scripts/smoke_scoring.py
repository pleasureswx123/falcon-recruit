"""Phase 4 画像评分冒烟：
构造含 Gap 的简历文本 + 职位 criteria → 跑完整流水线 → 校验 report 结构完整。

执行：
    cd backend
    ./.venv/Scripts/python.exe scripts/smoke_scoring.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas.job import (  # noqa: E402
    JobCriteria,
    SalaryRange,
    SkillRequirement,
)
from app.services.interview_advisor import (  # noqa: E402
    generate_questions,
    generate_questions_async,
)
from app.services.llm import is_enabled  # noqa: E402
from app.services.resume_parser import parse_resume, parse_resume_async  # noqa: E402
from app.services.resume_verifier import verify_profile  # noqa: E402
from app.services.scoring_engine import (  # noqa: E402
    compose_strengths_weaknesses,
    score_candidate,
)


RESUME = """
张三  后端工程师
电话：13800138000  邮箱：zhangsan@example.com

自我评价
5 年后端开发经验，擅长高并发架构，有沟通能力和团队协作意识。

工作经历
2018.07-2020.06 ABC 科技有限公司 · 后端工程师
  - 负责订单系统开发
2021.03-2023.02 XYZ 互联网公司 · 高级后端工程师
  - 主导微服务拆分
2023.05-至今 PQR 云服务公司 · 架构师
  - 负责云原生平台

教育经历
2014.09-2018.06 北京大学 计算机 本科

专业技能
Python、Java、Redis、Docker、Kubernetes、PostgreSQL

求职意向
期望 35-50K 北京
"""


def main() -> int:
    criteria = JobCriteria(
        education="bachelor",
        years_min=3,
        years_max=None,
        skills=[
            SkillRequirement(name="Python", level="required", weight=10),
            SkillRequirement(name="Go", level="required", weight=8),
            SkillRequirement(name="Redis", level="preferred", weight=5),
            SkillRequirement(name="Kubernetes", level="preferred", weight=6),
        ],
        industries=["互联网"],
        soft_skills=["沟通能力", "团队协作"],
        salary=SalaryRange(min=30, max=45),
        location="北京",
    )

    profile = parse_resume(RESUME)
    print(
        f"[profile] name={profile.name}  total_years={profile.total_years}  "
        f"degree={profile.highest_degree}  skills={profile.skills}"
    )
    assert profile.total_years >= 4.5, "解析的累计年限应 >= 4.5 年"
    assert "Python" in profile.skills, "应命中 Python 技能"
    assert len(profile.experiences) == 3, f"应识别 3 段工作经历, got {len(profile.experiences)}"

    verification = verify_profile(profile)
    print(
        f"[verify] gaps={len(verification.gaps)}  "
        f"avg_tenure={verification.average_tenure_months}  "
        f"risk={verification.risk_flags}"
    )
    assert len(verification.gaps) >= 1, "应识别到 2020.06 -> 2021.03 的 9 月 Gap"
    assert any("断层" in r for r in verification.risk_flags), "应标记断层风险"

    dims, total = score_candidate(profile, verification, criteria)
    print(f"[score] total={total}")
    for d in dims:
        print(f"  - {d.label:8s}  {d.score:3d}  (w={d.weight})  {d.reason}")
    assert 0 <= total <= 100
    assert len(dims) == 5
    dim_keys = {d.dimension for d in dims}
    assert dim_keys == {
        "hard_requirements",
        "professional_background",
        "stability",
        "soft_skills",
        "expectation_fit",
    }
    # 缺 Go 技能 → hard_requirements 应扣分
    hard = next(d for d in dims if d.dimension == "hard_requirements")
    assert any("Go" in c for c in hard.concerns), "应提示缺少 Go 技能"

    strengths, weaknesses = compose_strengths_weaknesses(dims)
    print(f"[summary] strengths={strengths}")
    print(f"[summary] weaknesses={weaknesses}")
    assert len(strengths) + len(weaknesses) > 0

    questions = generate_questions(dims, profile, criteria, verification)
    print(f"[interview/template] {len(questions)} questions:")
    for q in questions:
        print(f"  · [{q.topic}] {q.question}")
    assert len(questions) == 3, f"模板版应生成 3 条面试题, got {len(questions)}"

    # LLM 版面试助手：key 未配置时内部会自动降级到模板版，仍应返回 3 条
    llm_questions = asyncio.run(
        generate_questions_async(
            dims, profile, criteria, verification,
            job_title="高级后端工程师",
            weaknesses=weaknesses,
        )
    )
    engine = "llm" if is_enabled() else "template-fallback"
    print(f"[interview/async · {engine}] {len(llm_questions)} questions:")
    for q in llm_questions:
        intent_hint = f"  ({q.intent})" if q.intent else ""
        print(f"  · [{q.topic}] {q.question}{intent_hint}")
    assert len(llm_questions) == 3, (
        f"async 面试助手应生成 3 条题目, got {len(llm_questions)}"
    )

    # 简历解析 async 版：LLM 开时走 LLM；未开时应与 regex 结果完全一致
    parser_engine = "llm" if is_enabled() else "regex-fallback"
    async_profile = asyncio.run(parse_resume_async(RESUME, fallback_name="张三"))
    print(
        f"[resume/async · {parser_engine}] name={async_profile.name}  "
        f"phone={async_profile.phone}  total_years={async_profile.total_years}  "
        f"skills={async_profile.skills[:6]}"
    )
    assert async_profile.name, "async 简历解析应至少返回姓名"
    assert async_profile.phone, "async 简历解析应补出手机号"
    assert async_profile.total_years > 0, "async 简历解析应返回累计年限"

    print("\n[smoke] ✅ ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
