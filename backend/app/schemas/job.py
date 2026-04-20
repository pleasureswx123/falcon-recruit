"""职位相关的 API 数据契约。

JobCriteria 结构对齐 PRD §3.4 五维评分模型：
  1. 硬性条件 (education / years)
  2. 专业背景 (skills / industries)
  3. 稳定性    (min_tenure_months)
  4. 软技能    (soft_skills)
  5. 期望契合  (salary / location)
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.job import JobStatus


EducationLevel = Literal["unlimited", "college", "bachelor", "master", "phd"]
SkillLevel = Literal["required", "preferred", "bonus"]


class SkillRequirement(BaseModel):
    """技能项要求。"""

    name: str = Field(min_length=1, max_length=60)
    level: SkillLevel = Field(default="preferred", description="必要程度")
    weight: int = Field(default=5, ge=1, le=10, description="权重 1-10")


class SalaryRange(BaseModel):
    """期望薪资区间(单位：K/月)。"""

    min: int | None = Field(default=None, ge=0)
    max: int | None = Field(default=None, ge=0)


class JobCriteria(BaseModel):
    """AI 生成 / 人工微调的结构化匹配基准。"""

    model_config = ConfigDict(extra="ignore")

    # 1. 硬性条件
    education: EducationLevel = Field(default="unlimited")
    years_min: int = Field(default=0, ge=0, le=40)
    years_max: int | None = Field(default=None, ge=0, le=40)

    # 2. 专业背景
    skills: list[SkillRequirement] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)

    # 3. 稳定性
    min_tenure_months: int | None = Field(
        default=None, ge=0, description="期望候选人平均在职时长(月)"
    )

    # 4. 软技能
    soft_skills: list[str] = Field(default_factory=list)

    # 5. 期望契合
    salary: SalaryRange = Field(default_factory=SalaryRange)
    location: str | None = Field(default=None, max_length=60)


class JobBase(BaseModel):
    """职位共享字段。"""

    title: str = Field(min_length=1, max_length=120, description="职位名称")
    raw_jd: str = Field(min_length=1, description="原始 JD 文本")


class JobCreate(JobBase):
    """创建职位请求体。

    criteria 可由前端提供；若为空则后端自动调用 jd_parser mock 生成。
    """

    criteria: JobCriteria | None = Field(
        default=None, description="结构化匹配基准；留空由后端自动解析"
    )
    status: JobStatus = Field(default=JobStatus.ACTIVE)


class JobUpdate(BaseModel):
    """更新职位请求体（全部字段可选）。"""

    model_config = ConfigDict(extra="ignore")

    title: str | None = Field(default=None, min_length=1, max_length=120)
    raw_jd: str | None = Field(default=None, min_length=1)
    criteria: JobCriteria | None = None
    status: JobStatus | None = None


class JobRead(BaseModel):
    """职位返回体。"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    raw_jd: str
    criteria: JobCriteria
    status: JobStatus
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    """分页列表响应。"""

    total: int
    items: list[JobRead]
