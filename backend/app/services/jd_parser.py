"""JD 文本 → 结构化匹配基准。

Phase 2：规则匹配实现。
Phase 6：接入 LLM 语义解析，env 有 OPENAI_API_KEY 则优先走 LLM，失败回落规则式。
"""
from __future__ import annotations

import logging
import re

from pydantic import ValidationError

from app.schemas.job import EducationLevel, JobCriteria, SalaryRange, SkillRequirement
from app.services.llm import chat_json, is_enabled
from app.services.llm.prompts import (
    JD_GEN_SYSTEM,
    JD_PARSE_SYSTEM,
    build_jd_gen_user,
    build_jd_parse_user,
)

logger = logging.getLogger(__name__)


# 常见技术栈关键词（大小写不敏感匹配）
_TECH_KEYWORDS: list[tuple[str, list[str]]] = [
    ("Python", ["python"]),
    ("Java", [r"\bjava\b"]),
    ("Go", [r"\bgolang\b", r"\bgo\b"]),
    ("JavaScript", ["javascript", r"\bjs\b"]),
    ("TypeScript", ["typescript", r"\bts\b"]),
    ("React", ["react", "reactjs"]),
    ("Vue", ["vue", "vuejs"]),
    ("Next.js", ["next.js", "nextjs"]),
    ("Node.js", ["node.js", "nodejs"]),
    ("FastAPI", ["fastapi"]),
    ("Django", ["django"]),
    ("Spring", ["spring boot", "springboot", "spring"]),
    ("PostgreSQL", ["postgresql", "postgres"]),
    ("MySQL", ["mysql"]),
    ("Redis", ["redis"]),
    ("MongoDB", ["mongodb", "mongo"]),
    ("Docker", ["docker"]),
    ("Kubernetes", ["kubernetes", r"\bk8s\b"]),
    ("AWS", [r"\baws\b"]),
    ("CI/CD", ["ci/cd", "cicd", "jenkins"]),
]

_SOFT_SKILL_KEYWORDS: list[tuple[str, list[str]]] = [
    ("沟通能力", ["沟通", "communication"]),
    ("团队协作", ["团队协作", "团队合作", "teamwork"]),
    ("问题解决", ["解决问题", "problem solving"]),
    ("学习能力", ["学习能力", "快速学习"]),
    ("领导力", ["领导", "leadership", "带团队"]),
]


def _find_education(text: str) -> EducationLevel:
    t = text.lower()
    if any(k in text for k in ("博士", "phd")):
        return "phd"
    if any(k in text for k in ("硕士", "研究生", "master")):
        return "master"
    if any(k in text for k in ("本科", "bachelor")) or "学士" in text:
        return "bachelor"
    if any(k in text for k in ("大专", "专科", "college")):
        return "college"
    return "unlimited"


def _find_years(text: str) -> tuple[int, int | None]:
    """提取工作年限范围。"""
    # e.g. "3-5年"、"3年以上"、"5年+"
    m = re.search(r"(\d+)\s*[-~到]\s*(\d+)\s*年", text)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d+)\s*年\s*(以上|\+)", text)
    if m:
        return int(m.group(1)), None
    m = re.search(r"(\d+)\s*年", text)
    if m:
        return int(m.group(1)), None
    return 0, None


def _find_salary(text: str) -> SalaryRange:
    """提取薪资 K/月 区间。"""
    m = re.search(r"(\d{1,3})\s*[-~到]\s*(\d{1,3})\s*[kK]", text)
    if m:
        return SalaryRange(min=int(m.group(1)), max=int(m.group(2)))
    return SalaryRange()


def _find_location(text: str) -> str | None:
    cities = ["北京", "上海", "深圳", "广州", "杭州", "成都", "南京", "武汉", "西安", "苏州", "远程"]
    for city in cities:
        if city in text:
            return city
    return None


def _collect_by_keywords(
    text: str, groups: list[tuple[str, list[str]]]
) -> list[str]:
    """按关键词分组命中，返回去重后的标签名。"""
    lower = text.lower()
    hits: list[str] = []
    for name, patterns in groups:
        for p in patterns:
            if re.search(p, lower):
                hits.append(name)
                break
    return hits


def parse_jd_to_criteria(raw_jd: str) -> JobCriteria:
    """将 JD 文本解析为结构化匹配基准(mock)。"""
    if not raw_jd or not raw_jd.strip():
        return JobCriteria()

    years_min, years_max = _find_years(raw_jd)

    skill_names = _collect_by_keywords(raw_jd, _TECH_KEYWORDS)
    skills = [
        SkillRequirement(
            name=name,
            level="required" if idx < 3 else "preferred",
            weight=8 if idx < 3 else 5,
        )
        for idx, name in enumerate(skill_names)
    ]

    return JobCriteria(
        education=_find_education(raw_jd),
        years_min=years_min,
        years_max=years_max,
        skills=skills,
        industries=[],
        min_tenure_months=None,
        soft_skills=_collect_by_keywords(raw_jd, _SOFT_SKILL_KEYWORDS),
        salary=_find_salary(raw_jd),
        location=_find_location(raw_jd),
    )


def _coerce_llm_criteria(raw: dict) -> JobCriteria | None:
    """LLM 返回字典 → JobCriteria，容错字段类型偏差。"""
    if not isinstance(raw, dict):
        return None
    try:
        return JobCriteria.model_validate(raw)
    except ValidationError as exc:
        logger.warning("LLM JD 输出与 JobCriteria 不兼容，尝试字段修正：%s", exc)

    # 尝试剥离非法字段 / 强转
    safe: dict = {}
    if isinstance(raw.get("education"), str):
        safe["education"] = raw["education"]
    for k in ("years_min", "years_max", "min_tenure_months"):
        v = raw.get(k)
        if isinstance(v, (int, float)):
            safe[k] = int(v)
    skills_raw = raw.get("skills")
    if isinstance(skills_raw, list):
        safe_skills = []
        for s in skills_raw:
            if isinstance(s, dict) and s.get("name"):
                safe_skills.append(
                    {
                        "name": str(s["name"])[:60],
                        "level": s.get("level") or "preferred",
                        "weight": int(s.get("weight") or 5),
                    }
                )
        safe["skills"] = safe_skills
    for list_key in ("industries", "soft_skills"):
        v = raw.get(list_key)
        if isinstance(v, list):
            safe[list_key] = [str(x)[:40] for x in v if x]
    sal = raw.get("salary")
    if isinstance(sal, dict):
        safe["salary"] = {
            "min": sal.get("min") if isinstance(sal.get("min"), int) else None,
            "max": sal.get("max") if isinstance(sal.get("max"), int) else None,
        }
    if isinstance(raw.get("location"), str):
        safe["location"] = raw["location"][:60]

    try:
        return JobCriteria.model_validate(safe)
    except ValidationError as exc:
        logger.warning("LLM JD 字段修正仍失败：%s", exc)
        return None


async def generate_jd_async(title: str, description: str) -> str:
    """调用 LLM 根据职位名称与简单描述生成完整 JD 文本。

    未配置 LLM 时抛出 RuntimeError，由调用方处理并返回 HTTP 错误。
    """
    if not is_enabled():
        raise RuntimeError("LLM 未配置，无法使用 AI 生成 JD 功能。请联系管理员配置 API Key。")

    data = await chat_json(
        system=JD_GEN_SYSTEM,
        user=build_jd_gen_user(title, description),
        temperature=0.7,
        max_tokens=2500,
    )
    if isinstance(data, dict) and data.get("jd_text"):
        return str(data["jd_text"]).strip()

    raise RuntimeError("AI 返回格式异常，请稍后重试。")


async def parse_jd_to_criteria_async(
    raw_jd: str, title_hint: str | None = None
) -> JobCriteria:
    """LLM 优先 + 规则式降级。任何异常都不会把请求打挂。"""
    if not raw_jd or not raw_jd.strip():
        return JobCriteria()

    if is_enabled():
        try:
            data = await chat_json(
                system=JD_PARSE_SYSTEM,
                user=build_jd_parse_user(raw_jd, title_hint),
                temperature=0.1,
                max_tokens=1500,
            )
            if isinstance(data, dict):
                parsed = _coerce_llm_criteria(data)
                if parsed is not None:
                    return parsed
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM JD 解析异常，降级规则式：%s", exc)

    return parse_jd_to_criteria(raw_jd)
