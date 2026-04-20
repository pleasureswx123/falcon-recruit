"""简历结构化画像 + AI 五维评分 + 履历核验 DTO (TDD §3.2, PRD §3.3/3.4)。

所有字段都进入 Candidate.report JSON，由前端详情页直接可视化。
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ===================== 结构化简历画像 =====================


class WorkExperience(BaseModel):
    """单段工作经历。日期为 YYYY-MM 字符串，缺失置 None。"""

    company: str | None = None
    title: str | None = None
    start: str | None = None
    end: str | None = None  # None 视为"至今"
    description: str | None = None


class EducationExperience(BaseModel):
    school: str | None = None
    degree: Literal[
        "unlimited", "college", "bachelor", "master", "phd"
    ] = "unlimited"
    major: str | None = None
    start: str | None = None
    end: str | None = None


class ResumeProfile(BaseModel):
    """从简历原文抽取出来的结构化画像。"""

    name: str | None = None
    phone: str | None = None
    email: str | None = None
    location: str | None = None
    expected_salary: str | None = None
    expected_location: str | None = None

    total_years: float = 0.0  # 累计工作年限（根据工作经历汇总）
    highest_degree: Literal[
        "unlimited", "college", "bachelor", "master", "phd"
    ] = "unlimited"

    skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)

    experiences: list[WorkExperience] = Field(default_factory=list)
    educations: list[EducationExperience] = Field(default_factory=list)

    summary: str | None = None  # 自评 / 简介


# ===================== 履历核验 =====================


class CareerGap(BaseModel):
    """两段工作间的空窗期。"""

    from_end: str | None  # 上一段结束时间
    to_start: str | None  # 下一段开始时间
    months: int
    is_covered_by_education: bool = False
    note: str | None = None


class VerificationReport(BaseModel):
    """履历时间轴核验。"""

    gaps: list[CareerGap] = Field(default_factory=list)
    average_tenure_months: float = 0.0  # 平均在职时长（月）
    job_hopper: bool = False  # 平均在职 < 12 月视为频繁跳槽
    risk_flags: list[str] = Field(default_factory=list)


# ===================== 五维评分 =====================


ScoreDimension = Literal[
    "hard_requirements",  # 硬性条件（学历/年限/技能硬指标）
    "professional_background",  # 专业背景（行业、项目、技能深度）
    "stability",  # 稳定性（在职时长、Gap）
    "soft_skills",  # 软技能
    "expectation_fit",  # 期望契合度（薪资、地点）
]


class DimensionScore(BaseModel):
    """单维度得分（0-100）+ 理由 + 亮点/不足。"""

    dimension: ScoreDimension
    label: str  # 维度中文名
    score: int = Field(ge=0, le=100)
    weight: int = Field(ge=0, le=100)  # 各维度权重（合计 100）
    reason: str
    highlights: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)


class InterviewQuestion(BaseModel):
    topic: str  # 针对的弱项
    question: str
    intent: str | None = None  # LLM 生成时携带的考察意图，模板降级时为空


class CandidateReport(BaseModel):
    """落到 Candidate.report 的完整报告。"""

    version: int = 1
    profile: ResumeProfile = Field(default_factory=ResumeProfile)
    verification: VerificationReport = Field(default_factory=VerificationReport)
    dimensions: list[DimensionScore] = Field(default_factory=list)
    total_score: int = 0
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    interview_questions: list[InterviewQuestion] = Field(default_factory=list)
    generated_at: str | None = None  # ISO 时间
    engine: str = "rule-mock-v1"  # 后续接入 LLM 时可改为 "gpt-4o" 等
