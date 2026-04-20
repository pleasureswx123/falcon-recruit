"""简历文本 → ResumeProfile 结构化画像 (TDD §3.2 的前置步骤)。

规则式 mock 实现；后续可替换为 LLM 语义抽取。策略：
1. 按常见分节关键词切分 section（工作经历 / 教育经历 / 项目 / 技能 / 自我评价）。
2. 每个 section 里再按"时间段出现的行"作为子项切割点。
3. 用关键词表识别学历 / 技能 / 软技能；兜底不抛异常。
"""
from __future__ import annotations

import re
from typing import Iterable

from app.schemas.profile import (
    EducationExperience,
    ResumeProfile,
    WorkExperience,
)
from app.services.jd_parser import _SOFT_SKILL_KEYWORDS, _TECH_KEYWORDS

# ---------- 分节关键词 ----------
_SECTION_PATTERNS: dict[str, list[str]] = {
    "work": ["工作经历", "工作经验", "职业经历", "实习经历", "work experience"],
    "education": ["教育经历", "教育背景", "学历", "education"],
    "project": ["项目经历", "项目经验", "project experience", "projects"],
    "skill": ["专业技能", "技能清单", "个人技能", "skills"],
    "summary": ["自我评价", "个人简介", "个人优势", "summary", "about me"],
    "expect": ["求职意向", "期望", "求职目标"],
}

# ---------- 时间段正则 ----------
# 支持：2020.03-2022.06 / 2020-03~2022-06 / 2020/3-至今 / 2020年3月-2022年6月
_DATE = r"(\d{4})[\.\-/年]\s*(\d{1,2})?[\.\-/月]?"
_RANGE_RE = re.compile(
    rf"({_DATE})\s*[\-~至到到—–]\s*(?:({_DATE})|至今|now|present|Present)",
    re.IGNORECASE,
)


def _norm_ym(year: str | None, month: str | None) -> str | None:
    if not year:
        return None
    if not month:
        return f"{year}-01"
    return f"{int(year):04d}-{int(month):02d}"


def _find_ranges(text: str) -> list[tuple[str | None, str | None]]:
    out: list[tuple[str | None, str | None]] = []
    for m in _RANGE_RE.finditer(text):
        start = _norm_ym(m.group(2), m.group(3))
        end_year = m.group(5)
        end_month = m.group(6)
        end = _norm_ym(end_year, end_month) if end_year else None
        out.append((start, end))
    return out


def _split_sections(text: str) -> dict[str, str]:
    """把原文切成 {section_key: body_text}。未命中则归入 summary。"""
    sections: dict[str, str] = {}
    # 建立反查：关键词 -> section_key
    index: list[tuple[int, str]] = []
    for key, kws in _SECTION_PATTERNS.items():
        for kw in kws:
            for m in re.finditer(re.escape(kw), text, re.IGNORECASE):
                index.append((m.start(), key))
    index.sort()
    if not index:
        sections["summary"] = text
        return sections
    for i, (pos, key) in enumerate(index):
        end = index[i + 1][0] if i + 1 < len(index) else len(text)
        sections.setdefault(key, "")
        sections[key] += text[pos:end] + "\n"
    # 开头未归类的作为 summary
    if index[0][0] > 0:
        sections.setdefault("summary", "")
        sections["summary"] = text[: index[0][0]] + "\n" + sections.get("summary", "")
    return sections


def _pick_degree(text: str) -> str:
    if any(k in text for k in ("博士", "phd")):
        return "phd"
    if any(k in text for k in ("硕士", "研究生", "master")):
        return "master"
    if any(k in text for k in ("本科", "bachelor", "学士")):
        return "bachelor"
    if any(k in text for k in ("大专", "专科", "college")):
        return "college"
    return "unlimited"


_DEGREE_ORDER = {"unlimited": 0, "college": 1, "bachelor": 2, "master": 3, "phd": 4}


def _collect(patterns: list[tuple[str, list[str]]], text: str) -> list[str]:
    lower = text.lower()
    hits: list[str] = []
    for name, keys in patterns:
        for p in keys:
            if re.search(p, lower):
                hits.append(name)
                break
    return hits


def _split_items(block: str) -> Iterable[str]:
    """按包含时间段的行做切割，返回每段子项。"""
    lines = block.splitlines()
    chunks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if _RANGE_RE.search(line) and current and any(l.strip() for l in current):
            chunks.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append(current)
    for c in chunks:
        yield "\n".join(c).strip()


def _months_between(start: str | None, end: str | None) -> int:
    if not start:
        return 0
    try:
        sy, sm = [int(x) for x in start.split("-")]
    except ValueError:
        return 0
    if end is None:
        from datetime import datetime

        now = datetime.now()
        ey, em = now.year, now.month
    else:
        try:
            ey, em = [int(x) for x in end.split("-")]
        except ValueError:
            return 0
    months = (ey - sy) * 12 + (em - sm)
    return max(months, 0)


def _parse_experiences(block: str) -> list[WorkExperience]:
    exps: list[WorkExperience] = []
    for item in _split_items(block):
        ranges = _find_ranges(item)
        if not ranges:
            continue
        start, end = ranges[0]
        # 尝试第一行提取 company & title
        first_line = next(
            (l for l in item.splitlines() if l.strip() and _RANGE_RE.search(l)),
            item.splitlines()[0] if item.splitlines() else "",
        )
        cleaned = _RANGE_RE.sub("", first_line).strip(" |·,，-")
        parts = re.split(r"[\s\|·,，\-]+", cleaned, maxsplit=1)
        company = parts[0] if parts else None
        title = parts[1] if len(parts) > 1 else None
        exps.append(
            WorkExperience(
                company=company or None,
                title=title or None,
                start=start,
                end=end,
                description=item[:300],
            )
        )
    return exps


def _parse_educations(block: str) -> list[EducationExperience]:
    eds: list[EducationExperience] = []
    for item in _split_items(block):
        ranges = _find_ranges(item)
        if not ranges:
            continue
        start, end = ranges[0]
        school_line = next(
            (l for l in item.splitlines() if l.strip() and _RANGE_RE.search(l)),
            "",
        )
        cleaned = _RANGE_RE.sub("", school_line).strip(" |·,，-")
        parts = re.split(r"[\s\|·,，\-]+", cleaned, maxsplit=1)
        school = parts[0] if parts else None
        major = parts[1] if len(parts) > 1 else None
        eds.append(
            EducationExperience(
                school=school or None,
                major=major or None,
                degree=_pick_degree(item),
                start=start,
                end=end,
            )
        )
    return eds


def parse_resume(text: str) -> ResumeProfile:
    """从简历全文抽取 ResumeProfile。永不抛异常，失败返回空 profile。"""
    profile = ResumeProfile()
    if not text or not text.strip():
        return profile

    sections = _split_sections(text)

    # 工作经历
    if "work" in sections:
        profile.experiences = _parse_experiences(sections["work"])
    # 教育
    if "education" in sections:
        profile.educations = _parse_educations(sections["education"])
    if not profile.educations:
        # 全文兜底识别最高学历
        profile.highest_degree = _pick_degree(text)
    else:
        profile.highest_degree = max(
            (e.degree for e in profile.educations), key=lambda d: _DEGREE_ORDER[d]
        )

    # 技能 / 软技能：优先 skill section，否则全文
    skill_src = sections.get("skill", "") or text
    profile.skills = _collect(_TECH_KEYWORDS, skill_src)
    profile.soft_skills = _collect(_SOFT_SKILL_KEYWORDS, text)

    # 累计工作年限
    total_months = sum(_months_between(e.start, e.end) for e in profile.experiences)
    profile.total_years = round(total_months / 12, 1)

    # 期望
    expect_block = sections.get("expect", "")
    m = re.search(r"(\d{1,3})\s*[-~到]\s*(\d{1,3})\s*[kK]", expect_block)
    if m:
        profile.expected_salary = f"{m.group(1)}-{m.group(2)}K"
    for city in ("北京", "上海", "深圳", "广州", "杭州", "成都", "远程"):
        if city in expect_block:
            profile.expected_location = city
            break

    # 自评
    summary = sections.get("summary", "").strip()
    if summary:
        profile.summary = summary[:500]

    return profile



# ===================== LLM 接入（Phase 6） =====================

import logging  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from app.services.llm import chat_json, is_enabled  # noqa: E402
from app.services.llm.prompts import (  # noqa: E402
    RESUME_PARSE_SYSTEM,
    build_resume_parse_user,
)

_logger = logging.getLogger(__name__)

_ALLOWED_DEGREES = {"unlimited", "college", "bachelor", "master", "phd"}
_ALLOWED_SOFT_SKILLS = {
    "沟通能力", "团队协作", "问题解决", "学习能力", "领导力",
}


def _norm_ym_str(value) -> str | None:
    """兜底规范化 LLM 返回的日期字段为 YYYY-MM；无法解析返回 None。"""
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s or s.lower() in {"至今", "now", "present", "none", "null"}:
        return None
    m = re.match(r"^(\d{4})[\-/\.年]?\s*(\d{1,2})?[\-/\.月]?", s)
    if not m:
        return None
    year = int(m.group(1))
    month = int(m.group(2)) if m.group(2) else 1
    if not (1 <= month <= 12):
        month = 1
    return f"{year:04d}-{month:02d}"


def _coerce_llm_profile(raw: dict) -> ResumeProfile | None:
    """LLM JSON → ResumeProfile；字段缺失/类型异常尽量兜底，整体失败返回 None。"""
    if not isinstance(raw, dict):
        return None

    safe: dict = {}
    for key in ("name", "phone", "email", "location",
                "expected_salary", "expected_location", "summary"):
        v = raw.get(key)
        if isinstance(v, str) and v.strip() and v.strip().lower() not in {"null", "none"}:
            safe[key] = v.strip()[:500 if key == "summary" else 120]

    ty = raw.get("total_years")
    if isinstance(ty, (int, float)) and ty >= 0:
        safe["total_years"] = round(float(ty), 1)

    deg = raw.get("highest_degree")
    if isinstance(deg, str) and deg in _ALLOWED_DEGREES:
        safe["highest_degree"] = deg

    skills_raw = raw.get("skills")
    if isinstance(skills_raw, list):
        safe["skills"] = [str(x)[:40] for x in skills_raw if x][:40]

    soft_raw = raw.get("soft_skills")
    if isinstance(soft_raw, list):
        safe["soft_skills"] = [str(x)[:20] for x in soft_raw if x and str(x) in _ALLOWED_SOFT_SKILLS][:10]

    exps_raw = raw.get("experiences")
    if isinstance(exps_raw, list):
        exps: list[dict] = []
        for item in exps_raw[:20]:
            if not isinstance(item, dict):
                continue
            exps.append({
                "company": (str(item.get("company"))[:80] if item.get("company") else None),
                "title": (str(item.get("title"))[:80] if item.get("title") else None),
                "start": _norm_ym_str(item.get("start")),
                "end": _norm_ym_str(item.get("end")),
                "description": (
                    str(item.get("description"))[:300]
                    if item.get("description") else None
                ),
            })
        safe["experiences"] = exps

    edus_raw = raw.get("educations")
    if isinstance(edus_raw, list):
        edus: list[dict] = []
        for item in edus_raw[:10]:
            if not isinstance(item, dict):
                continue
            deg = item.get("degree")
            edus.append({
                "school": (str(item.get("school"))[:80] if item.get("school") else None),
                "major": (str(item.get("major"))[:80] if item.get("major") else None),
                "degree": deg if isinstance(deg, str) and deg in _ALLOWED_DEGREES else "unlimited",
                "start": _norm_ym_str(item.get("start")),
                "end": _norm_ym_str(item.get("end")),
            })
        safe["educations"] = edus

    try:
        return ResumeProfile.model_validate(safe)
    except ValidationError as exc:
        _logger.warning("LLM ResumeProfile 校验失败：%s", exc)
        return None


async def parse_resume_async(
    text: str, fallback_name: str | None = None
) -> ResumeProfile:
    """LLM 优先 + regex 回落的简历画像解析。永不抛异常。"""
    if not text or not text.strip():
        return ResumeProfile()

    if is_enabled():
        try:
            data = await chat_json(
                system=RESUME_PARSE_SYSTEM,
                user=build_resume_parse_user(text, fallback_name),
                temperature=0.1,
                max_tokens=2500,
            )
            if isinstance(data, dict):
                parsed = _coerce_llm_profile(data)
                if parsed is not None:
                    # 累计年限：LLM 没给就用工作经历重新算，保证与 scoring 一致
                    if parsed.total_years <= 0 and parsed.experiences:
                        total_months = sum(
                            _months_between(e.start, e.end)
                            for e in parsed.experiences
                        )
                        parsed.total_years = round(total_months / 12, 1)
                    return parsed
        except Exception as exc:  # noqa: BLE001
            _logger.warning("LLM 简历解析异常，降级 regex：%s", exc)

    return parse_resume(text)
