# 【猎鹰】智能招聘管理系统 - 技术方案文档 (TDD)

## 1. 系统架构 (System Architecture)
本项目采用 **Monorepo** 架构，将前后端代码存放于同一仓库，便于 AI 进行全栈上下文理解与接口对齐。

*   **前端 (frontend/)**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Shadcn UI.
*   **后端 (backend/)**: FastAPI (Python 3.10+), SQLAlchemy/SQLModel (ORM).
*   **数据库**: PostgreSQL (主存储), Redis (处理异步分拣任务状态).
*   **AI 引擎**: 火山方舟 Doubao-1.5-Pro-32K（通过 OpenAI 兼容接口调用）。全流程 5 个调用点：AI 辅助写 JD、JD 结构化解析、**简历画像结构化**、五维语义评分、**面试提纲生成（含考察意图）**，详见 §3.3。
*   **文件解析**:
    - `PyMuPDF (fitz)`: 提取 PDF 文本流。
    - `python-docx`: 提取 Word 文本。
    - `python-magic`: 准确识别文件 MIME 类型，防止后缀名篡改。

---

## 2. 数据库建模 (Data Schema)

### 2.1 Jobs (职位表)
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | UUID | 主键 |
| `title` | String | 职位名称 (如: 高级前端开发) |
| `raw_jd` | Text | 原始 JD 文本内容 |
| `criteria` | JSONB | AI 生成的匹配基准（包含学历、年限、技术栈等权重配置） |
| `status` | Enum | `active` (进行中) / `closed` (已结束) |
| `created_at` | DateTime | 创建时间 |

### 2.2 Candidates (候选人表)
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | UUID | 主键 |
| `job_id` | UUID | 外键 -> Jobs.id |
| `name` | String | 从简历解析提取的姓名 |
| `phone` | String | 唯一标识符 (PII 提取的手机号) |
| `email` | String | 唯一标识符 (PII 提取的邮箱) |
| `score` | Integer | 综合匹配分 (0-100) |
| `report` | JSONB | AI 画像报告 (五维打分、优势、弱势、面试建议、断层标记) |
| `is_verified` | Boolean | 是否经过人工手动纠偏校对 |

### 2.3 Files (文件附件表)
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | UUID | 主键 |
| `candidate_id` | UUID | 外键 -> Candidates.id |
| `file_type` | Enum | `RESUME` (简历) / `PORTFOLIO` (作品集) |
| `original_name`| String | 上传时的原始文件名（包含乱码） |
| `new_name` | String | 系统生成的标准文件名 (例: [张三-Java-简历].pdf) |
| `file_path` | String | 服务器物理存储路径 |

---

## 3. 核心技术逻辑 (Core Technical Logic)

### 3.1 乱码对抗：智能分拣算法 (PII-Linker)
**核心原则：** 彻底弃用文件名索引，强制进行文本内容探测。
1.  **文件流解析：** 异步读取上传 ZIP 内的所有文件内容。
2.  **特征提取：**
    - 使用正则 (Regex) 提取手机号、邮箱。
    - 使用 NLP 或特征匹配提取候选人姓名。
3.  **关联逻辑：**
    - 构建全局映射：`Map<PII_Key, Candidate_ID>`。
    - 若简历 A 提取的手机号与作品集 B 提取的手机号一致，则自动将两者绑定到同一 Candidate。
4.  **补偿机制：** 对于无法提取 PII 的文件，采用“同级文件夹聚类算法”进行辅助关联。

### 3.2 AI 语义评分与核验
1.  **结构化匹配：** 将解析后的候选人 JSON 与职位 `criteria` JSON 交给大模型进行语义比对（`SCORING_SYSTEM` prompt），而非关键词统计；模型异常 / 返回不符合约束时，`score_candidate_async` 自动回落到规则式 `score_candidate`。
2.  **时间轴断层核验：** 计算公式 `Gap = NextJob.StartDate - PrevJob.EndDate`，若 `Gap > 90 天` 且非教育衔接，在报告中插入“履历断层”风险项；此项逻辑为纯规则（`resume_verifier.py`），不依赖 LLM。
3.  **面试助手：** `generate_questions_async` 基于最低分的 3 个维度构造 prompt（`INTERVIEW_SYSTEM`），返回 3 条面试题及其考察意图；LLM 不可用降级为模板生成。
4.  **简历结构化增强：** `parse_resume_async` 优先让 LLM 抽取结构化画像（`RESUME_PARSE_SYSTEM`），校验失败或 LLM 未配置时回落到 regex 版 `parse_resume`，保持 PII 与累计年限计算一致性。

### 3.3 AI 在各阶段的使用 (AI Usage Map)
| 阶段 | 代码入口 | Prompt | 触发时机 | 失败降级 |
| :-: | :--- | :--- | :--- | :--- |
| 职位定义 · 写 JD | `jd_parser.generate_jd_async` | `JD_WRITE_SYSTEM` / `build_jd_write_user` | 职位创建页点击「AI 帮我写 JD」 | 抛 HTTP 500（不影响手写 JD） |
| 职位定义 · JD 结构化 | `jd_parser.parse_jd_to_criteria_async` | `JD_PARSE_SYSTEM` / `build_jd_parse_user` | JD 保存时或点击「AI 解析」 | `parse_jd_rule_based` 正则兜底 |
| 分拣流水线 · 简历画像 | `resume_parser.parse_resume_async` | `RESUME_PARSE_SYSTEM` / `build_resume_parse_user` | ZIP 任务进入 `_build_report_async` 之初 | `parse_resume` 正则兜底 |
| 分拣流水线 · 五维评分 | `scoring_engine.score_candidate_async` | `SCORING_SYSTEM` / `build_scoring_user` | 画像 + 核验结果就绪后 | `score_candidate` 规则兜底 |
| 分拣流水线 · 面试提纲 | `interview_advisor.generate_questions_async` | `INTERVIEW_SYSTEM` / `build_interview_user` | 五维评分完成后 | `generate_questions` 模板兜底 |

**统一约束：** 所有 LLM 调用走 `app/services/llm/chat_json`（强制 JSON 模式 + 超时 + 重试），结果由各自的 `_coerce_llm_*` 函数做 Pydantic 校验；只要 `OPENAI_API_KEY` 未配置或抛任何异常都会无感降级，接口永不因 LLM 故障宕机。

---

## 4. 关键 API 接口定义

| 方法 | 路径 | 功能 |
| :--- | :--- | :--- |
| `POST` | `/api/jobs` | 创建职位并同步生成 AI 结构化标准 |
| `POST` | `/api/jobs/generate-jd` | **AI 辅助写 JD**：输入职位名称与简单描述，返回完整 JD 文案（不落库） |
| `POST` | `/api/jobs/parse-jd` | **AI 解析 JD**：输入 JD 文本，返回结构化匹配基准 JSON（不落库，供前端预览） |
| `POST` | `/api/tasks/upload` | 上传 ZIP 包，启动异步分拣与解析任务 |
| `GET` | `/api/candidates` | 获取某职位下的所有候选人列表及简要评分 |
| `GET` | `/api/candidates/{id}/report` | 获取详尽的 AI 画像报告与面试建议 |
| `PATCH` | `/api/candidates/{id}` | 手动纠偏：调整关联文件或候选人基本信息 |
| `GET` | `/api/export/zip/{job_id}` | 批量导出重命名后的文件压缩包 |

---

## 5. 项目目录结构 (Project Structure)

```text
/falcon-recruit
├── /docs               # 核心文档 (PRD.md, TDD.md)
├── /frontend           # Next.js 14 前端
│   ├── /src
│   │   ├── /app        # 页面路由
│   │   ├── /components # 公用 UI 组件 (Shadcn)
│   │   └── /lib        # API 请求封装 (Axios/Fetch)
│   └── package.json
├── /backend            # FastAPI 后端
│   ├── /app
│   │   ├── /api        # 路由入口
│   │   ├── /models     # 数据库 SQLModel
│   │   ├── /services   # 业务逻辑 (PII分拣、AI评分)
│   │   └── /core       # 配置与数据库连接
│   ├── main.py         # 后端入口
│   └── requirements.txt
├── .augment            # Augment/AI 工具配置
└── README.md
```

---

## 7. 部署与运维 (Deployment)

本项目本地开发与服务器生产均使用 **docker-compose** 统一编排基础设施，代码零差异。

### 7.1 文件清单（仓库根目录）
- `docker-compose.yml` — 基础设施（PostgreSQL 16 + Redis 7），**本地和服务器共用**；DB/Redis 端口仅绑定 `127.0.0.1`，不对外暴露。
- `docker-compose.prod.yml` — 生产 override，追加 `backend` 与 `frontend` 容器；backend 走 compose 网络内的 `postgres`/`redis` 别名，与基础设施解耦。
- `.env.example` — compose 顶层环境变量模板（数据库账号密码、端口、LLM key、前端 API 基址等）。
- `backend/Dockerfile` + `.dockerignore` — 多阶段构建（python:3.12-slim，builder 含 `build-essential + libpq-dev`，runtime 仅保留 `libpq5 + curl`）。
- `frontend/Dockerfile` + `.dockerignore` — Next.js standalone 三阶段构建（`deps → builder → runner`），运行态仅携带 `standalone + static + public`。

### 7.2 日常用法

**本地开发（推荐：基础设施容器化 + 前后端宿主机热重载）**

```bash
# 仓库根目录
cp .env.example .env
docker compose up -d

# 后端
cd backend
cp .env.example .env   # 默认已指向 127.0.0.1:5432 的 falcon 库
./.venv/Scripts/python.exe -m uvicorn main:app --reload

# 前端
cd ../frontend
npm run dev
```

**服务器生产部署**

```bash
cp .env.example .env
# 编辑 .env：修改 POSTGRES_PASSWORD、OPENAI_API_KEY 等
# 注意：NEXT_PUBLIC_API_BASE_URL 仅生产环境使用，开发环境通过 next.config.mjs rewrites 代理
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 7.3 卷与持久化
| 卷 | 用途 |
| :--- | :--- |
| `postgres-data` | PostgreSQL 数据目录 |
| `redis-data`    | Redis AOF 持久化文件 |
| `backend-storage` | 生产模式下 backend 容器内 `/app/storage`（ZIP 解压物 / 导出文件） |

### 7.4 数据库迁移（SQLite → PostgreSQL）
开发期默认可继续用 SQLite（修改 backend `.env` 注释切换）；切到 PostgreSQL 后：
1. `docker compose up -d postgres` 起库；
2. 后端启动时 `init_db()` 通过 SQLModel 元数据自动建表（POC 阶段不接入 Alembic）；
3. 生产正式上线前再引入 `alembic` 做增量迁移；目前 requirements 里已预留条目。

### 7.5 故障自检
| 现象 | 排查步骤 |
| :--- | :--- |
| 后端连接 DB 超时 | `docker compose ps` 查看 `postgres` 是否 `(healthy)`；`docker compose logs postgres` 看初始化日志 |
| 前端镜像构建失败 | 确保 `frontend/next.config.mjs` 含 `output: "standalone"`（容器化必需） |
| LLM 接口未生效 | `docker compose exec backend env | grep OPENAI`，`OPENAI_API_KEY` 为空时按设计自动降级为规则式 |

---

## 6. 开发路线图 (Roadmap)

1.  **Phase 1 (基础框架):** 完成全局布局 (Sidebar/Header)，配置前端 Next.js 与后端 FastAPI 通信。
2.  **Phase 2 (职位管理):** 实现职位的 CRUD；包含两个 AI 子功能：
    - **AI 辅助写 JD**（`POST /api/jobs/generate-jd`）：零门槛生成招聘文案。
    - **AI 解析 JD**（`POST /api/jobs/parse-jd`）：将 JD 文本转为结构化匹配基准。
3.  **Phase 3 (分拣引擎):** 实现 ZIP 上传、文件解压、PII 提取与自动关联算法。
4.  **Phase 4 (画像评分):** 对接 LLM，实现五维评分模型与履历断层核验。
5.  **Phase 5 (工作台与导出):** 实现分拣纠偏 UI，支持重命名文件的批量下载。
