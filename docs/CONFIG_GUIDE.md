# 配置文件层级说明

本文档说明 Falcon AI 项目中所有配置文件的作用、优先级和使用场景。

## 📋 配置文件总览

```
项目根目录/
├── .env                    # Docker Compose 级别的环境变量（基础设施 + 生产配置）
├── .env.example            # 上述文件的模板
├── docker-compose.yml      # 基础服务（PostgreSQL + Redis）
├── docker-compose.prod.yml # 生产环境追加服务（backend + frontend + nginx）
│
└── backend/
    ├── .env                # 后端应用级别配置（仅本地开发使用）
    ├── .env.example        # 上述文件的模板
    ├── Dockerfile          # 后端容器构建文件
    └── app/core/config.py  # Python 配置类（pydantic-settings）
```

## 🎯 两套独立的配置体系

### 体系1：Docker Compose 级别（根目录）

**适用场景：**
- ✅ 生产部署：所有服务在容器中运行
- ✅ 本地开发：仅启动 PostgreSQL 和 Redis，后端/前端在宿主机运行

**配置文件：**
- `.env` - 实际配置（不提交到 Git）
- `.env.example` - 模板文件（提交到 Git）

**包含的配置项：**
```bash
# 基础设施
POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT
REDIS_PORT, REDIS_URL

# 生产服务
NGINX_PORT, MAX_UPLOAD_MB

# LLM 配置（注入到 backend 容器）
OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL
```

**优先级：** Docker Compose 环境变量 > config.py 默认值

---

### 体系2：后端应用级别（backend/）

**适用场景：**
- ✅ 本地开发：直接在宿主机运行 `uvicorn main:app`
- ❌ 生产环境：不使用（被 Docker Compose 覆盖）

**配置文件：**
- `backend/.env` - 实际配置（不提交到 Git）
- `backend/.env.example` - 模板文件（提交到 Git）
- `backend/app/core/config.py` - Python 配置类定义

**包含的配置项：**
```python
# 应用基础
APP_NAME, APP_ENV, APP_VERSION, DEBUG

# 服务监听
HOST, PORT

# 数据库（本地开发连接宿主机 PostgreSQL）
DATABASE_URL, DATABASE_ECHO

# Redis
REDIS_URL

# 存储
STORAGE_ROOT, MAX_UPLOAD_MB

# LLM
OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL
```

**优先级：** 环境变量 > `.env` 文件 > config.py 默认值

---

## 🔄 配置流向图

### 生产环境（Docker 部署）

```
根目录 .env
    ↓ (docker-compose 读取)
docker-compose.prod.yml
    ↓ (environment 注入)
backend 容器环境变量
    ↓ (pydantic-settings 读取，优先级最高)
config.py Settings 实例
    ↓
FastAPI 应用使用
```

**关键点：**
- `backend/.env` **不会被读取**（因为环境变量已设置）
- 所有敏感信息通过根目录 `.env` → docker-compose → 容器环境变量传递

---

### 本地开发环境

#### 方式A：混合模式（推荐）

```bash
# 终端1：启动基础设施
docker compose up -d

# 终端2：启动后端（读取 backend/.env）
cd backend && uvicorn main:app --reload

# 终端3：启动前端
cd frontend && npm run dev
```

**配置流向：**
```
backend/.env
    ↓ (pydantic-settings 读取)
config.py Settings 实例
    ↓
FastAPI 应用使用

注意：DATABASE_URL 需要指向 127.0.0.1:5432（宿主机映射端口）
```

#### 方式B：纯 Docker 模式

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

**配置流向：** 同生产环境

---

## ⚠️ 常见混淆点

### 1. LLM 配置在哪里设置？

**生产环境：**
- 在根目录 `.env` 中设置
- 通过 `docker-compose.prod.yml` 注入到 backend 容器
- `backend/.env` 中的配置**无效**

**本地开发：**
- 在 `backend/.env` 中设置
- 直接运行 `uvicorn` 时读取
- 根目录 `.env` 中的配置**不影响**后端

### 2. 数据库连接字符串为什么不同？

**生产环境（docker-compose.prod.yml 第29行）：**
```yaml
DATABASE_URL: postgresql+asyncpg://user:pass@postgres:5432/db
                                              ^^^^^^^^
                                              使用 Docker 网络服务名
```

**本地开发（backend/.env.example 第13行）：**
```bash
DATABASE_URL=postgresql+asyncpg://falcon:falcon_dev_pw@127.0.0.1:5432/falcon
                                                    ^^^^^^^^^^
                                                    使用宿主机 localhost
```

### 3. APP_ENV 和 DEBUG 在哪里控制？

**生产环境：**
- `docker-compose.prod.yml` 第24-25行显式设置
- `APP_ENV=production`, `DEBUG=false`

**本地开发：**
- `backend/.env` 或 `backend/.env.example` 中设置
- 默认 `APP_ENV=development`, `DEBUG=true`

**重要：** 这些变量**不在** config.py 的 `.env` 文件中加载，而是通过系统环境变量传递。

---

## 🔒 安全注意事项

### 1. API Key 管理

**❌ 错误做法：**
- 将真实的 `OPENAI_API_KEY` 提交到 Git
- 在 `.env.example` 中填写真实密钥

**✅ 正确做法：**
- `.env.example` 中留空或写占位符
- 真实的密钥只在 `.env` 文件中（已在 `.gitignore` 中）
- 生产环境通过安全的密钥管理服务注入

### 2. 数据库密码

**生产环境强制要求：**
```yaml
# docker-compose.prod.yml 第11-12行
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD required}
```
如果未设置，Docker Compose 会拒绝启动。

---

## 📝 快速参考

### 修改生产环境配置

1. 编辑根目录 `.env`
2. 重新部署：
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
   ```

### 修改本地开发配置

1. 编辑 `backend/.env`
2. 重启后端服务：
   ```bash
   # 停止旧的 uvicorn 进程
   # 重新启动
   cd backend && uvicorn main:app --reload
   ```

### 查看当前生效的配置

在后端代码中：
```python
from app.core.config import get_settings

settings = get_settings()
print(settings.app_env)      # 当前环境
print(settings.debug)        # 调试模式
print(settings.database_url) # 数据库连接
```

或在运行时访问：
```bash
curl http://localhost:8000/
# 返回 {"app": "Falcon AI", "env": "development", ...}
```

---

## 🎓 总结

| 配置位置 | 作用范围 | 优先级 | 使用场景 |
|---------|---------|--------|---------|
| 根目录 `.env` | Docker Compose | 高 | 生产部署 / 本地基础设施 |
| `backend/.env` | 后端应用 | 中 | 本地开发（直接运行 uvicorn） |
| `docker-compose.prod.yml` | 生产覆盖 | 高 | 生产环境变量注入 |
| `config.py` 默认值 | 兜底 | 低 | 未设置任何环境变量时使用 |

**核心原则：**
1. 生产环境只关心根目录 `.env` + `docker-compose.prod.yml`
2. 本地开发只关心 `backend/.env` + 根目录 `docker-compose.yml`
3. 两套体系互不干扰，但需要注意不要混淆
