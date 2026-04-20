"""面试助手：基于弱项维度生成 3 条针对性面试提纲 (PRD §3.4)。

双通道：
- `generate_questions`：纯模板式，永远可用的兜底版本。
- `generate_questions_async`：LLM 优先 + 模板降级，被 profile_pipeline 使用。
"""
from __future__ import annotations

import logging

from pydantic import ValidationError

from app.schemas.job import JobCriteria
from app.schemas.profile import (
    DimensionScore,
    InterviewQuestion,
    ResumeProfile,
    VerificationReport,
)
from app.services.llm import chat_json, is_enabled
from app.services.llm.prompts import INTERVIEW_SYSTEM, build_interview_user

logger = logging.getLogger(__name__)

# 维度 → 题库：选择得分最低的三个维度作为出题依据
_QUESTION_BANK: dict[str, list[str]] = {
    "hard_requirements": [
        "岗位对 {focus} 有明确要求，请结合你过去项目讲一个相关案例。",
        "你对 {focus} 的掌握深度如何？能否做系统设计或底层原理层面的讲解？",
    ],
    "professional_background": [
        "请简述你最有成就感的一个项目，重点说说你负责的技术模块。",
        "你如何在团队里持续深耕 {focus} 这类技术栈？",
    ],
    "stability": [
        "在 {from_end} 到 {to_start} 这段时间你主要在做什么？"
        "这段经历对你的职业发展产生了什么影响？",
        "从过往经历看你的在职时长偏短，下一份工作你希望从公司获得什么以保持稳定？",
    ],
    "soft_skills": [
        "请举例说明一次你运用 {focus} 帮助团队或项目达成目标的经历。",
        "当你与同事出现分歧时，你通常如何处理？",
    ],
    "expectation_fit": [
        "你对当前的薪资与工作地点期望是如何形成的？如有落差你如何权衡？",
        "如果岗位需要你阶段性到 {focus} 工作，你能否接受？",
    ],
}


def _pick_focus(
    dim_key: str,
    profile: ResumeProfile,
    criteria: JobCriteria,
    verification: VerificationReport,
) -> dict[str, str]:
    """根据维度从 criteria / profile 里挑一个具象的"焦点词"用于填模板。"""
    ctx = {"focus": "该能力"}
    if dim_key == "hard_requirements":
        required = [
            s.name for s in criteria.skills if s.level == "required"
        ] or [s.name for s in criteria.skills]
        if required:
            have = {s.lower() for s in profile.skills}
            miss = [s for s in required if s.lower() not in have]
            ctx["focus"] = miss[0] if miss else required[0]
    elif dim_key == "professional_background":
        if criteria.skills:
            ctx["focus"] = criteria.skills[0].name
    elif dim_key == "soft_skills":
        needed = criteria.soft_skills or profile.soft_skills
        if needed:
            ctx["focus"] = needed[0]
    elif dim_key == "expectation_fit":
        ctx["focus"] = criteria.location or "异地"
    elif dim_key == "stability":
        gaps = [g for g in verification.gaps if not g.is_covered_by_education]
        if gaps:
            ctx["from_end"] = gaps[0].from_end or "—"
            ctx["to_start"] = gaps[0].to_start or "—"
    return ctx


def generate_questions(
    dimensions: list[DimensionScore],
    profile: ResumeProfile,
    criteria: JobCriteria,
    verification: VerificationReport,
) -> list[InterviewQuestion]:
    """挑得分最低的三个维度，各出一道题；若不足 3 个弱项则用默认题补齐。"""
    weak = sorted(dimensions, key=lambda d: d.score)[:3]
    out: list[InterviewQuestion] = []
    seen: set[str] = set()

    for dim in weak:
        ctx = _pick_focus(dim.dimension, profile, criteria, verification)
        bank = _QUESTION_BANK.get(dim.dimension, [])
        for tpl in bank:
            try:
                q = tpl.format(**ctx)
            except KeyError:
                q = tpl
            if q not in seen:
                out.append(InterviewQuestion(topic=dim.label, question=q))
                seen.add(q)
                break
        if len(out) >= 3:
            break

    # 兜底
    defaults = [
        InterviewQuestion(
            topic="综合素质",
            question="请简述你对应聘岗位的理解，以及你认为自己最匹配的 3 个优势。",
        ),
        InterviewQuestion(
            topic="职业规划",
            question="未来 1-3 年你希望在哪些方向深耕？",
        ),
    ]
    for d in defaults:
        if len(out) >= 3:
            break
        if d.question not in seen:
            out.append(d)
            seen.add(d.question)

    return out[:3]



# ===================== LLM 接入（Phase 6） =====================

# dimension → 中文标签（与 scoring_engine 对齐，避免互相 import）
_DIM_LABEL: dict[str, str] = {
    "hard_requirements": "硬性条件",
    "professional_background": "专业背景",
    "stability": "稳定性",
    "soft_skills": "软技能",
    "expectation_fit": "期望契合度",
}


def _coerce_llm_questions(raw: dict) -> list[InterviewQuestion] | None:
    """LLM 输出 → InterviewQuestion 列表。不足 3 条或字段异常返回 None。"""
    if not isinstance(raw, dict):
        return None
    items = raw.get("questions")
    if not isinstance(items, list):
        return None

    out: list[InterviewQuestion] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        q_text = str(item.get("question") or "").strip()
        if not q_text or q_text in seen:
            continue
        dim_key = str(item.get("dimension") or "").strip()
        topic = _DIM_LABEL.get(dim_key) or (dim_key or "综合素质")
        intent = item.get("intent")
        intent_text = str(intent).strip() if isinstance(intent, str) and intent.strip() else None
        try:
            out.append(
                InterviewQuestion(topic=topic, question=q_text, intent=intent_text)
            )
        except ValidationError as exc:
            logger.warning("LLM 面试题字段异常，跳过：%s", exc)
            continue
        seen.add(q_text)
        if len(out) >= 3:
            break

    return out if len(out) >= 3 else None


async def generate_questions_async(
    dimensions: list[DimensionScore],
    profile: ResumeProfile,
    criteria: JobCriteria,
    verification: VerificationReport,
    *,
    job_title: str,
    weaknesses: list[str] | None = None,
) -> list[InterviewQuestion]:
    """LLM 优先生成 3 条面试提纲；未配置 key / 返回异常 → 回落模板版。"""
    if is_enabled():
        # 选最低 3 个维度作为弱项维度，并组装自然语言描述
        weak = sorted(dimensions, key=lambda d: d.score)[:3]
        weak_dims = [d.dimension for d in weak]
        concern_lines: list[str] = list(weaknesses or [])
        if not concern_lines:
            for d in weak:
                for c in d.concerns[:2]:
                    concern_lines.append(f"{d.label}：{c}")
        try:
            data = await chat_json(
                system=INTERVIEW_SYSTEM,
                user=build_interview_user(
                    job_title=job_title,
                    weaknesses=concern_lines,
                    weak_dimensions=weak_dims,
                ),
                temperature=0.4,
                max_tokens=1000,
            )
            if isinstance(data, dict):
                parsed = _coerce_llm_questions(data)
                if parsed is not None:
                    return parsed
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM 面试提纲异常，降级模板：%s", exc)

    return generate_questions(dimensions, profile, criteria, verification)
