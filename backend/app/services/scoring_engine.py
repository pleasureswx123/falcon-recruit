"""五维评分引擎 (PRD §3.4, TDD §3.2)。

维度与权重（合计 100）：
    hard_requirements       25  硬性条件（学历 / 年限 / 必需技能）
    professional_background 25  专业背景（技能深度 / 软硬技能命中）
    stability               20  稳定性（平均在职 / Gap 数量）
    soft_skills             15  软技能
    expectation_fit         15  期望契合度（薪资 / 地点）

规则式 mock 实现；接入 LLM 时替换 `score_candidate` 主体即可。
"""
from __future__ import annotations

from app.schemas.job import EducationLevel, JobCriteria
from app.schemas.profile import (
    DimensionScore,
    ResumeProfile,
    VerificationReport,
)

_DEGREE_RANK: dict[EducationLevel, int] = {
    "unlimited": 0,
    "college": 1,
    "bachelor": 2,
    "master": 3,
    "phd": 4,
}

_DIM_WEIGHT = {
    "hard_requirements": 25,
    "professional_background": 25,
    "stability": 20,
    "soft_skills": 15,
    "expectation_fit": 15,
}

_DIM_LABEL = {
    "hard_requirements": "硬性条件",
    "professional_background": "专业背景",
    "stability": "稳定性",
    "soft_skills": "软技能",
    "expectation_fit": "期望契合度",
}


def _score_hard(profile: ResumeProfile, criteria: JobCriteria) -> DimensionScore:
    highlights: list[str] = []
    concerns: list[str] = []
    score = 100

    # 学历
    need = _DEGREE_RANK[criteria.education]
    have = _DEGREE_RANK[profile.highest_degree]
    if need > 0:
        if have >= need:
            highlights.append(f"学历达标（{profile.highest_degree}）")
        else:
            score -= 25
            concerns.append(
                f"学历未达要求：期望 {criteria.education}，实际 {profile.highest_degree}"
            )

    # 年限
    if criteria.years_min > 0:
        if profile.total_years + 0.5 >= criteria.years_min:
            highlights.append(f"工作年限 {profile.total_years} 年满足要求")
        else:
            gap = criteria.years_min - profile.total_years
            score -= min(40, int(gap * 12))
            concerns.append(
                f"年限不足：期望 ≥ {criteria.years_min} 年，实际 {profile.total_years} 年"
            )

    # 必需技能命中率
    required = [s for s in criteria.skills if s.level == "required"]
    if required:
        have = {s.lower() for s in profile.skills}
        hit = [s for s in required if s.name.lower() in have]
        miss = [s for s in required if s.name.lower() not in have]
        ratio = len(hit) / len(required)
        score -= int((1 - ratio) * 40)
        if hit:
            highlights.append(
                f"命中必需技能 {len(hit)}/{len(required)}：{'、'.join(s.name for s in hit)}"
            )
        if miss:
            concerns.append(
                f"缺少必需技能：{'、'.join(s.name for s in miss)}"
            )

    return DimensionScore(
        dimension="hard_requirements",
        label=_DIM_LABEL["hard_requirements"],
        score=max(0, min(100, score)),
        weight=_DIM_WEIGHT["hard_requirements"],
        reason="学历 / 年限 / 必需技能综合评估",
        highlights=highlights,
        concerns=concerns,
    )


def _score_professional(
    profile: ResumeProfile, criteria: JobCriteria
) -> DimensionScore:
    have = {s.lower() for s in profile.skills}
    all_skills = criteria.skills
    hit = [s for s in all_skills if s.name.lower() in have]
    total_weight = sum(s.weight for s in all_skills) or 1
    got_weight = sum(s.weight for s in hit)
    ratio = got_weight / total_weight if all_skills else 0.6
    score = int(40 + 55 * ratio)  # 40-95 基础分
    # 额外加分：命中技能数量
    score = min(100, score + min(5, len(hit)))

    highlights: list[str] = []
    concerns: list[str] = []
    if hit:
        highlights.append(f"技能覆盖度 {int(ratio * 100)}%")
    missing = [s.name for s in all_skills if s.name.lower() not in have]
    if missing:
        concerns.append(f"未命中技能：{'、'.join(missing[:5])}")

    return DimensionScore(
        dimension="professional_background",
        label=_DIM_LABEL["professional_background"],
        score=score,
        weight=_DIM_WEIGHT["professional_background"],
        reason="基于职位技能权重的加权命中率",
        highlights=highlights,
        concerns=concerns,
    )



def _score_stability(
    profile: ResumeProfile, verification: VerificationReport
) -> DimensionScore:
    score = 100
    highlights: list[str] = []
    concerns: list[str] = []

    avg = verification.average_tenure_months
    if avg > 0:
        if avg >= 24:
            highlights.append(f"平均在职 {avg:.1f} 个月，稳定性良好")
        elif avg >= 12:
            score -= 15
            concerns.append(f"平均在职 {avg:.1f} 个月，偏短")
        else:
            score -= 35
            concerns.append(f"平均在职仅 {avg:.1f} 个月，频繁跳槽")

    real_gaps = [g for g in verification.gaps if not g.is_covered_by_education]
    if real_gaps:
        score -= min(30, 10 * len(real_gaps))
        concerns.append(
            f"识别到 {len(real_gaps)} 段履历断层，合计 "
            f"{sum(g.months for g in real_gaps)} 个月"
        )
    else:
        highlights.append("履历连续无显著断层")

    return DimensionScore(
        dimension="stability",
        label=_DIM_LABEL["stability"],
        score=max(0, min(100, score)),
        weight=_DIM_WEIGHT["stability"],
        reason="平均在职时长与 Gap 综合",
        highlights=highlights,
        concerns=concerns,
    )


def _score_soft(profile: ResumeProfile, criteria: JobCriteria) -> DimensionScore:
    need = set(criteria.soft_skills or [])
    have = set(profile.soft_skills or [])
    if not need:
        score = 75
        reason = "职位未显式要求软技能"
        highlights = [f"候选人提到：{'、'.join(have)}"] if have else []
        concerns: list[str] = []
    else:
        hit = need & have
        ratio = len(hit) / len(need)
        score = int(50 + 45 * ratio)
        reason = f"软技能命中 {len(hit)}/{len(need)}"
        highlights = [f"匹配：{'、'.join(hit)}"] if hit else []
        concerns = [f"未提及：{'、'.join(need - have)}"] if (need - have) else []

    return DimensionScore(
        dimension="soft_skills",
        label=_DIM_LABEL["soft_skills"],
        score=score,
        weight=_DIM_WEIGHT["soft_skills"],
        reason=reason,
        highlights=highlights,
        concerns=concerns,
    )


def _score_expectation(
    profile: ResumeProfile, criteria: JobCriteria
) -> DimensionScore:
    import re as _re

    score = 85
    highlights: list[str] = []
    concerns: list[str] = []

    if criteria.location and profile.expected_location:
        if criteria.location == profile.expected_location:
            highlights.append(f"期望地点匹配：{criteria.location}")
        else:
            score -= 25
            concerns.append(
                f"地点不一致：职位 {criteria.location} / 候选人 {profile.expected_location}"
            )
    elif criteria.location and not profile.expected_location:
        concerns.append("候选人未说明期望地点")
        score -= 5

    exp = profile.expected_salary or ""
    jmin = criteria.salary.min
    jmax = criteria.salary.max
    if jmin and jmax and exp:
        m = _re.search(r"(\d+)\s*-\s*(\d+)", exp)
        if m:
            emin, emax = int(m.group(1)), int(m.group(2))
            if emax <= jmax and emin >= jmin - 3:
                highlights.append(f"薪资期望在职位区间内（{exp}）")
            elif emin > jmax:
                score -= 30
                concerns.append(f"薪资偏高：期望 {exp}，职位 {jmin}-{jmax}K")
            else:
                score -= 10
                concerns.append(f"薪资略有偏差：期望 {exp}，职位 {jmin}-{jmax}K")

    return DimensionScore(
        dimension="expectation_fit",
        label=_DIM_LABEL["expectation_fit"],
        score=max(0, min(100, score)),
        weight=_DIM_WEIGHT["expectation_fit"],
        reason="薪资与地点期望对齐度",
        highlights=highlights,
        concerns=concerns,
    )


def score_candidate(
    profile: ResumeProfile,
    verification: VerificationReport,
    criteria: JobCriteria,
) -> tuple[list[DimensionScore], int]:
    """返回五维评分列表 + 加权总分（0-100 整数）。"""
    dims = [
        _score_hard(profile, criteria),
        _score_professional(profile, criteria),
        _score_stability(profile, verification),
        _score_soft(profile, criteria),
        _score_expectation(profile, criteria),
    ]
    total = sum(d.score * d.weight for d in dims) / 100
    return dims, int(round(total))


def compose_strengths_weaknesses(
    dimensions: list[DimensionScore],
) -> tuple[list[str], list[str]]:
    """按得分排序，抽取 top 优势与 top 弱势。"""
    ordered = sorted(dimensions, key=lambda d: d.score, reverse=True)
    strengths = [f"{d.label}：{h}" for d in ordered[:3] for h in d.highlights[:2]]
    weaknesses = [
        f"{d.label}：{c}" for d in reversed(ordered) for c in d.concerns[:2]
    ][:5]
    return strengths, weaknesses


# ===================== LLM 接入（Phase 6） =====================

import logging  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from app.services.llm import chat_json, is_enabled  # noqa: E402
from app.services.llm.prompts import SCORING_SYSTEM, build_scoring_user  # noqa: E402

_logger = logging.getLogger(__name__)

_DIM_ORDER: tuple[str, ...] = tuple(_DIM_WEIGHT.keys())


def _coerce_llm_dimensions(raw: dict) -> tuple[list[DimensionScore], int] | None:
    """LLM 评分 JSON → DimensionScore 列表 + 总分。"""
    if not isinstance(raw, dict):
        return None
    dims_raw = raw.get("dimensions")
    if not isinstance(dims_raw, list):
        return None

    by_dim: dict[str, DimensionScore] = {}
    for item in dims_raw:
        if not isinstance(item, dict):
            continue
        name = item.get("dimension")
        if name not in _DIM_WEIGHT:
            continue
        try:
            ds = DimensionScore(
                dimension=name,
                label=_DIM_LABEL[name],
                score=max(0, min(100, int(item.get("score") or 0))),
                weight=_DIM_WEIGHT[name],
                reason=str(item.get("reason") or _DIM_LABEL[name]),
                highlights=[str(x) for x in (item.get("highlights") or [])][:5],
                concerns=[str(x) for x in (item.get("concerns") or [])][:5],
            )
        except (ValidationError, TypeError, ValueError) as exc:
            _logger.warning("LLM 维度解析失败 %s: %s", name, exc)
            continue
        by_dim[name] = ds

    if len(by_dim) < 5:
        return None

    dims = [by_dim[k] for k in _DIM_ORDER]
    total_from_llm = raw.get("total")
    if isinstance(total_from_llm, int) and 0 <= total_from_llm <= 100:
        total = total_from_llm
    else:
        total = int(round(sum(d.score * d.weight for d in dims) / 100))
    return dims, total


async def score_candidate_async(
    profile: ResumeProfile,
    verification: VerificationReport,
    criteria: JobCriteria,
    job_title: str,
) -> tuple[list[DimensionScore], int, str]:
    """LLM 优先 + 规则式降级。返回 (dims, total, engine_name)。"""
    if is_enabled():
        try:
            data = await chat_json(
                system=SCORING_SYSTEM,
                user=build_scoring_user(
                    job_title=job_title,
                    criteria_json=criteria.model_dump_json(),
                    profile_json=profile.model_dump_json(),
                    verification_json=verification.model_dump_json(),
                ),
                temperature=0.2,
                max_tokens=2000,
            )
            if isinstance(data, dict):
                parsed = _coerce_llm_dimensions(data)
                if parsed is not None:
                    dims, total = parsed
                    return dims, total, "llm"
        except Exception as exc:  # noqa: BLE001
            _logger.warning("LLM 评分异常，降级规则式：%s", exc)

    dims, total = score_candidate(profile, verification, criteria)
    return dims, total, "rule-mock-v1"
