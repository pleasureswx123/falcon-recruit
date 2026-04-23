# 猎鹰 Falcon AI · 智能招聘管理系统

> HR 拖一个 ZIP，AI 还你一份可读的人才报告。

从「乱码压缩包」到「结构化人才报告」的一站式智能招聘流水线：自动解压 → PII 关联 → 物理重命名 → 简历画像 → 五维评分 → 面试提纲，全链路无感降级、零宕机风险。

---

## ✨ 核心能力

| 阶段 | AI 能力 | 触发点 | 降级策略 |
| :-: | :--- | :--- | :--- |
| 1 | **AI 写 JD** | 职位创建页「AI 帮我写 JD」 | 直接报错提示 |
| 2 | **JD → 结构化匹配基准** | 保存 JD / 点击「AI 解析」 | 正则关键词解析 |
| 3 | **简历文本 → 结构化画像** | ZIP 分拣后画像流水线 | 正则抽取 `parse_resume` |
| 4 | **五维语义评分** | 画像 + 基准生成候选人报告 | 规则式 `score_candidate` |
| 5 | **面试提纲（带考察意图）** | 报告生成后 | 模板题库 `generate_questions` |

> LLM 默认走火山方舟 Doubao 1.5 Pro（OpenAI 兼容协议），任何一环 LLM 不可达均自动降级。

---

## 🏗️ 仓库结构

```
falcon-recruit/
├── backend/                       # FastAPI + SQLModel + PyMuPDF
│   ├── app/                       # 业务代码（api/services/schemas/core）
│   ├── scripts/                   # smoke 脚本（smoke_jobs/smoke_scoring/smoke_phase5）
│   ├── Dockerfile                 # 多阶段 · python:3.12-slim
│   └── requirements.txt
├── frontend/                      # Next.js 14 + Tailwind + Shadcn UI
│   ├── src/                       # app router / components / lib
│   └── Dockerfile                 # 多阶段 · Next.js standalone
├── docs/                          # PRD / TDD / 用户操作手册
├── docker-compose.yml             # 基础设施：postgres + redis
├── docker-compose.prod.yml        # 生产 override：前后端容器
└── .env.example                   # 根变量模板
```

---

## 🚀 快速开始

### 先决条件
- Docker Desktop ≥ 24
- Node.js ≥ 20 + npm（仅本地开发模式需要）
- Python ≥ 3.10（仅本地开发模式需要）

### 模式 A · 本地开发（仅容器化基础设施，推荐日常使用）

```bash
# 1) 克隆并配置
git clone git@github.com:pleasureswx123/falcon-recruit.git
cd falcon-recruit
cp .env.example .env
cp backend/.env.example backend/.env        # 填入 OPENAI_API_KEY 可选
cp frontend/.env.local.example frontend/.env.local

# 2) 起基础设施（Postgres + Redis）
docker compose up -d

# 3) 启动后端（另开一个终端）
cd backend
python -m venv .venv && .\.venv\Scripts\activate      # Windows
# source .venv/bin/activate                            # macOS / Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 4) 启动前端（再开一个终端）
cd frontend
npm install
npm run dev                # http://localhost:3000

Remove-Item -Recurse -Force .next
```

### 模式 B · 全栈容器化（服务器部署 / 演示）

```bash
cp .env.example .env                # 编辑密码、LLM key、API_BASE_URL
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 查看服务状态
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
# 访问地址: http://<host>:80  (通过 Nginx 统一入口)
# 前端页面: http://<host>/
# 后端 API: http://<host>/api/
# API 文档: http://<host>/api/docs
```

**架构说明：**
- **Nginx** 作为反向代理，统一处理所有请求
- `/` → 前端 Next.js 应用
- `/api/` → 后端 FastAPI 服务
- 彻底解决跨域问题，前后端在同一域名下

**验证部署：**
```bash
# Linux/macOS
bash scripts/verify_nginx.sh

# Windows PowerShell
.\scripts\verify_nginx.ps1
```

---

## 🔑 环境变量速查

| 变量 | 用途 | 默认 |
| :-- | :-- | :-- |
| `POSTGRES_USER/PASSWORD/DB` | Postgres 账号 | falcon / falcon_dev_pw / falcon |
| `POSTGRES_PORT` / `REDIS_PORT` | 宿主机映射端口 | 5432 / 6379 |
| `DATABASE_URL` | 后端数据库（compose 内部自动注入） | `postgresql+asyncpg://…` |
| `REDIS_URL` | Redis 连接 | `redis://127.0.0.1:6379/0` |
| `OPENAI_API_KEY` | LLM Key（留空即降级） | — |
| `OPENAI_BASE_URL` | LLM endpoint | 火山方舟 `/api/v3` |
| `LLM_MODEL` | 模型名 | `doubao-1-5-pro-32k-250115` |
| `NEXT_PUBLIC_API_BASE_URL` | 前端指向的后端 | `/api` (生产环境) |
| `NGINX_PORT` | Nginx 对外端口 | 80 |
| `MAX_UPLOAD_MB` | ZIP 上传上限 | 200 |

---

## 🧪 冒烟测试

```bash
cd backend
.\.venv\Scripts\python.exe scripts\smoke_jobs.py        # 职位 CRUD + AI 解析 JD
.\.venv\Scripts\python.exe scripts\smoke_scoring.py     # 画像 → 评分 → 面试 → 简历 LLM
.\.venv\Scripts\python.exe scripts\smoke_phase5.py      # Dashboard + 导出
```

均打印 `ALL PASS ✓` 即全绿。

---

## 📚 文档

- [`docs/PRD.md`](docs/PRD.md) — 产品需求文档（含 AI 能力全景矩阵）
- [`docs/TDD.md`](docs/TDD.md) — 技术设计文档（含 AI 调用链路、部署与运维）
- [`docs/用户操作手册.md`](docs/用户操作手册.md) — HR 端使用指南

---

## 🛠️ 技术栈

**Backend** · FastAPI · SQLModel · asyncpg · PyMuPDF · python-docx · OpenAI SDK (兼容火山方舟) · Pydantic v2
**Frontend** · Next.js 14 (App Router) · TypeScript · Tailwind · Shadcn UI · TanStack Query · Zustand · React Hook Form + Zod
**Infra** · PostgreSQL 16 · Redis 7 · Docker Compose

---

## 📄 License

内部项目，未开源授权。
