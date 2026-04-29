
---

## AI 全流程总览

```
创建职位 → 解析JD → 上传简历 → AI评分 → 生成面试题
   AI         AI                  AI        AI
```

---

## 阶段 1：AI 生成 JD（职位描述）

| 项目 | 内容 |
|------|------|
| **触发时机** | HR 创建职位时点击"AI 帮我写 JD" |
| **输入** | 职位名称 + 简单描述（如"需要一个 Python 后端，熟悉 FastAPI"） |
| **AI 做什么** | 根据简短描述，扩写成完整的职位描述文案 |
| **输出** | 完整的 JD 文本（职责、要求、加分项、福利等） |
| **对应函数** | 可能在 `app/services/jd_parser.py` 或类似文件 |

```
输入："Python后端，3年以上，熟悉FastAPI"
输出：
  【岗位职责】
  1. 负责公司核心业务系统的后端开发...
  【任职要求】
  1. 3年以上Python开发经验
  2. 精通FastAPI框架...
  【加分项】
  1. 有AI项目经验优先...
```

---

## 阶段 2：AI 解析 JD → 结构化匹配基准

| 项目 | 内容 |
|------|------|
| **触发时机** | JD 保存时或点击"AI 解析"按钮 |
| **输入** | 原始 JD 文本（可能是上面 AI 生成的，也可能是 HR 手写的） |
| **AI 做什么** | 从自然语言中提取出结构化的筛选条件 |
| **输出** | `JobCriteria` JSON（存在 `jobs.criteria` 字段） |
| **对应代码** | `parse_jd_to_criteria_async()` |

```python
# 你看到的这段代码
criteria: JobCriteria = payload.criteria or await parse_jd_to_criteria_async(
    payload.raw_jd, title_hint=payload.title
)
```

```
输入 JD 文本 → AI 解析 →
{
  "education": "本科",
  "experience_years": 3,
  "skills": [
    {"name": "Python", "required": true, "weight": 5},
    {"name": "FastAPI", "required": true, "weight": 4},
    {"name": "PostgreSQL", "required": false, "weight": 3}
  ],
  "soft_skills": ["沟通能力", "团队协作"],
  "salary_range": {"min": 15000, "max": 25000},
  "location": "北京"
}
```

---

## 阶段 3：AI 解析简历 → 结构化档案

| 项目 | 内容 |
|------|------|
| **触发时机** | `run_pipeline` 阶段 3.5，对每个候选人执行 |
| **输入** | 从 PDF/DOCX 提取出的简历纯文本 |
| **AI 做什么** | 从杂乱文本中提取结构化信息 |
| **输出** | `ResumeProfile`（姓名、技能、工作经历、学历等） |
| **对应代码** | `parse_resume_async()` |

```
输入："张三，男，5年Python开发，曾在字节跳动..."
→ AI 解析 →
{
  "name": "张三",
  "skills": ["Python", "FastAPI", "Docker"],
  "experiences": [
    {"company": "字节跳动", "role": "后端开发", "years": 3},
    {"company": "某创业公司", "role": "全栈开发", "years": 2}
  ],
  "education": {"degree": "本科", "major": "计算机科学"},
  "total_years": 5.0
}
```

---

## 阶段 4：AI 评分（最核心的 AI 调用）

| 项目 | 内容 |
|------|------|
| **触发时机** | `run_pipeline` 阶段 3.5，对每个候选人执行 |
| **输入** | ① 候选人 `ResumeProfile` ② 职位 `JobCriteria` ③ 职位名称 |
| **AI 做什么** | 逐维度对比候选人和职位要求，打分并写评语 |
| **输出** | 各维度得分 + 综合总分 |
| **对应代码** | `score_candidate_async()` |

```
输入：
  候选人：Python 5年 + FastAPI + Docker
  职位要求：Python + FastAPI + PostgreSQL，经验 3 年

→ AI 对比分析 →
dimensions = [
  {"name": "技能匹配", "score": 85, "comment": "Python/FastAPI 匹配，缺少 PostgreSQL"},
  {"name": "经验匹配", "score": 90, "comment": "5年经验，超过要求的3年"},
  {"name": "学历匹配", "score": 80, "comment": "本科，满足要求"},
]
total_score = 85
```

**这一步是整个系统的价值核心——把 HR 从几百份简历里解放出来。**

---

## 阶段 5：AI 生成面试问题

| 项目 | 内容 |
|------|------|
| **触发时机** | 评分完成后，对每个候选人执行 |
| **输入** | ① 各维度得分 ② 候选人短板 ③ 职位要求 |
| **AI 做什么** | 针对候选人的弱项生成量身定制的面试问题 |
| **输出** | 3 个左右的面试问题 |
| **对应代码** | `generate_questions_async()` |

```
输入：
  短板：["缺少 PostgreSQL 经验", "无团队管理经验"]
  职位：Python 后端工程师

→ AI 生成 →
interview_questions = [
  "你主要用 MySQL，如果项目需要迁移到 PostgreSQL，你会怎么规划？",
  "请描述一个你用 FastAPI 解决过的复杂业务场景",
  "你未来 1-2 年的技术成长规划是什么？"
]
```

---

## 五个阶段的输入输出总结

| 阶段 | 触发时机 | 输入 | AI 做什么 | 输出 | 降级方案 |
|------|---------|------|----------|------|---------|
| ① 生成 JD | HR 点击按钮 | 职位名 + 简述 | 扩写成完整 JD | JD 文本 | 无（可选手动写） |
| ② 解析 JD | JD 保存时 | JD 文本 | 提取结构化条件 | `JobCriteria` JSON | HR 手动填表单 |
| ③ 解析简历 | 分拣流水线 | 简历文本 | 提取结构化档案 | `ResumeProfile` | 正则 `parse_resume()` |
| ④ 评分 | 分拣流水线 | 档案 + 职位要求 | 逐维度对比打分 | 各维度得分 + 总分 | 规则引擎 `score_candidate()` |
| ⑤ 出面试题 | 分拣流水线 | 评分 + 短板 | 生成针对性问题 | 3 个面试问题 | 模板 `generate_questions()` |

---

## 降级保证

**AI 只是锦上添花，不是系统命脉。** 每一层都有降级：

```
AI 挂了？
  解析简历 → 用正则
  评分     → 用规则引擎
  出题     → 用固定模板
  解析JD   → HR 手动填
```