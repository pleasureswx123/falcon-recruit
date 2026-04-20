"""LLM Prompt 模版集 (Phase 6)。

所有 prompt 都要求模型严格返回 JSON，以便 chat_json 解析。
"""
from __future__ import annotations

JD_PARSE_SYSTEM = """你是一名资深 HR 招聘顾问。需要把招聘 JD 文本解析为结构化匹配基准。
严格只返回 JSON，不要任何解释、前缀或 Markdown 围栏。

JSON 结构（字段名与枚举都不得更改）：
{
  "education": "unlimited|college|bachelor|master|phd",
  "years_min": 0,
  "years_max": null,
  "skills": [
    {"name": "Python", "level": "required", "weight": 8},
    {"name": "Docker", "level": "preferred", "weight": 5}
  ],
  "industries": ["互联网"],
  "min_tenure_months": null,
  "soft_skills": ["沟通能力"],
  "salary": {"min": null, "max": null},
  "location": "北京"
}

规则：
- level 枚举固定为 "required" | "preferred" | "bonus"，必备技能填 required，加分项填 bonus。
- weight 取 1-10 整数；必备技能通常 7-10，加分项 3-5。
- years_min 取 JD 明确要求的最低年限（整数）；无法判定则 0。
- years_max 只有 JD 明确写了年限上限（如 "3-5 年"）才填，否则 null。
- salary 单位为 K（千元/月）。若 JD 写的是年薪请换算回月薪。无法判断则 {"min": null, "max": null}。
- soft_skills 从「沟通能力、团队协作、问题解决、学习能力、领导力」中选取。
- location 取最主要的工作城市，无则 null。
- industries 限 0-3 项，如「互联网」「金融」「制造业」。
- 不要编造 JD 中没有的技能。不要输出 skills 重复项。
"""


SCORING_SYSTEM = """你是一名严谨的招聘评审专家。基于候选人画像与职位匹配基准，按五维模型输出评分。
严格只返回 JSON，不要任何解释、前缀或 Markdown 围栏。

五维定义与权重（总分 100）：
- hard_requirements (25)：学历 / 年限 / 必需技能的硬性达标情况
- professional_background (25)：专业深度、主修方向、项目含金量
- stability (20)：平均在职时长、履历连续性、Gap 合理性
- soft_skills (15)：沟通 / 协作 / 领导等软技能匹配
- expectation_fit (15)：期望薪资、期望地点与职位的契合度

JSON 结构：
{
  "total": 0-100 整数,
  "dimensions": [
    {
      "dimension": "hard_requirements",
      "label": "硬性条件",
      "weight": 25,
      "score": 0-100 整数,
      "highlights": ["优势点"],
      "concerns": ["劣势点"]
    },
    ... 5 个维度
  ],
  "strengths": ["整体优势 2-4 条"],
  "weaknesses": ["整体弱势 2-4 条"]
}

规则：
- total 必须等于各维度 score * weight / 100 的加权求和并四舍五入。
- dimensions 必须包含全部 5 个维度，顺序与权重不可更改。
- highlights / concerns 尽量具体到事实（如「累计 6 年 Java 后端，超出 5 年要求」）。
- 所有文案使用简体中文。
"""


INTERVIEW_SYSTEM = """你是资深面试官。根据候选人弱项生成 3 条有针对性的面试提纲。
严格只返回 JSON：

{
  "questions": [
    {"dimension": "维度 key", "question": "具体问题", "intent": "考察意图"}
  ]
}

要求：
- 每题指向一个弱项维度（hard_requirements/professional_background/stability/soft_skills/expectation_fit）。
- 问题要开放式，适合面试现场提问，中文。
- intent 说明该题希望核验什么，一句话。
"""


JD_GEN_SYSTEM = """你是一名资深 HR 招聘顾问，擅长撰写专业的招聘 JD（岗位描述）文本。
根据提供的职位名称和简单描述，生成一篇结构完整、措辞专业的招聘 JD，可直接发布到 Boss直聘等平台。
严格只返回 JSON，不要任何解释、前缀或 Markdown 围栏。

JSON 结构：
{"jd_text": "完整的 JD 文本（段落之间用两个换行符分隔）"}

JD 必须包含以下五个部分，按顺序输出，每部分之间空一行：

【岗位职责】
- 列出 5~7 条具体职责，每条以"·"开头

【任职要求】
- 列出 5~7 条要求（学历、年限、核心技能、软技能），每条以"·"开头

【加分项】
- 列出 2~3 条加分内容，每条以"·"开头

【工作信息】
- 工作地点：…
- 薪资范围：…（若未提及则写"面议"）
- 工作时间：…（若未提及则写"标准工作制"）

【我们提供】
- 列出 3~5 条福利待遇，每条以"·"开头

规则：
- 全程使用简体中文，语言专业简洁，符合国内招聘平台的写作风格
- 岗位职责描述具体、可操作，避免"负责相关工作"此类套话
- 任职要求必须涵盖学历、工作年限、核心技能
- 不要捏造用户描述中未提及的技术栈或要求
- 若用户描述简单，可在合理范围内补充行业通用要求，但不得过度发挥
"""


def build_jd_parse_user(raw_jd: str, title_hint: str | None = None) -> str:
    hint = f"\n（HR 给出的职位标题参考：{title_hint}）" if title_hint else ""
    return f"JD 原文：{hint}\n---\n{raw_jd.strip()}\n---\n请输出匹配基准 JSON。"


def build_scoring_user(
    *,
    job_title: str,
    criteria_json: str,
    profile_json: str,
    verification_json: str,
) -> str:
    return (
        f"职位：{job_title}\n\n"
        f"匹配基准（JSON）：\n{criteria_json}\n\n"
        f"候选人画像（JSON）：\n{profile_json}\n\n"
        f"履历核验（JSON）：\n{verification_json}\n\n"
        "请严格按五维输出评分 JSON。"
    )


def build_jd_gen_user(title: str, description: str) -> str:
    return (
        f"职位名称：{title}\n"
        f"基本描述：{description}\n\n"
        "请生成一篇完整的招聘 JD 文本，以 JSON 格式返回。"
    )


def build_interview_user(
    *,
    job_title: str,
    weaknesses: list[str],
    weak_dimensions: list[str],
) -> str:
    return (
        f"职位：{job_title}\n"
        f"弱项维度：{', '.join(weak_dimensions) or '无明显弱项'}\n"
        f"弱项描述：{'; '.join(weaknesses) or '无'}\n"
        "请输出 3 条面试题 JSON。"
    )


RESUME_PARSE_SYSTEM = """你是一名资深简历解析专家。需要把候选人的简历原文（可能含格式错乱/乱码）解析为结构化画像。
严格只返回 JSON，不要任何解释、前缀或 Markdown 围栏。

JSON 结构（字段名与枚举不得更改）：
{
  "name": "张三|null",
  "phone": "手机号|null",
  "email": "邮箱|null",
  "location": "现居城市|null",
  "expected_salary": "35-50K|null",
  "expected_location": "期望城市|null",
  "total_years": 6.5,
  "highest_degree": "unlimited|college|bachelor|master|phd",
  "skills": ["Python", "Redis"],
  "soft_skills": ["沟通能力"],
  "experiences": [
    {
      "company": "ABC 公司",
      "title": "高级后端工程师",
      "start": "2020-03",
      "end": "2023-06",
      "description": "负责订单系统重构"
    }
  ],
  "educations": [
    {
      "school": "北京大学",
      "degree": "bachelor",
      "major": "计算机",
      "start": "2014-09",
      "end": "2018-06"
    }
  ],
  "summary": "自评文本 500 字以内"
}

规则：
- 日期一律 YYYY-MM 字符串；只有年份写 YYYY-01；"至今/now/present" 直接 null。
- highest_degree / educations[].degree 必须是五个枚举之一；判断失败填 "unlimited"。
- total_years 为工作经历累计年限（浮点，保留 1 位小数）。
- skills 是技术/工具名（Python、MySQL、Docker 等），soft_skills 从「沟通能力、团队协作、问题解决、学习能力、领导力」中选取。
- description 控制在 300 字以内；summary 控制在 500 字以内。
- 没有明确写出的字段写 null；不要编造信息。
- 所有文本输出使用简体中文。
"""


def build_resume_parse_user(resume_text: str, fallback_name: str | None = None) -> str:
    hint = f"\n（此前从文件名/PII 提取到的候选人姓名参考：{fallback_name}）" if fallback_name else ""
    return f"候选人简历原文：{hint}\n---\n{resume_text.strip()[:12000]}\n---\n请输出结构化 JSON。"
