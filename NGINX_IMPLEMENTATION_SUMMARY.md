# Nginx 反向代理方案 - 实施总结

## 📋 概述

本次实施在生产环境中添加了 Nginx 作为反向代理，彻底解决了前后端跨域问题。所有请求通过统一的域名和端口访问，Nginx 负责将请求路由到对应的前端或后端服务。

## ✅ 已完成的工作

### 1. 核心配置文件

#### 1.1 Nginx 配置
- **文件**: `nginx.conf`
- **功能**: 
  - 前端代理: `/` → `frontend:3000`
  - 后端 API 代理: `/api/` → `backend:8000/api/`
  - 健康检查: `/api/health` → `backend:8000/api/health`
  - API 文档: `/api/docs` → `backend:8000/api/docs`
  - 上传大小限制: 200MB
  - 超时设置: 前端 60s, 后端 120s（支持 AI 长时间处理）

#### 1.2 Nginx Dockerfile
- **文件**: `Dockerfile.nginx`
- **基础镜像**: `nginx:1.25-alpine`
- **功能**: 构建 Nginx 容器镜像

### 2. Docker Compose 配置更新

#### 2.1 生产环境配置
- **文件**: `docker-compose.prod.yml`
- **主要变更**:
  - 添加 `nginx` 服务
  - 前端不再直接暴露端口，通过 Nginx 代理
  - 后端不再直接暴露端口，通过 Nginx 代理
  - 前端 `NEXT_PUBLIC_API_BASE_URL` 改为 `/api`（相对路径，仅生产环境使用）
  - 开发环境不使用此变量，前端通过 next.config.mjs 的 rewrites 代理

### 3. 环境变量配置

#### 3.1 环境变量模板
- **文件**: `.env.example`
- **新增配置**:
  ```env
  NGINX_PORT=80
  # 前端 API 地址（仅生产环境使用）
  NEXT_PUBLIC_API_BASE_URL=/api
  ```

### 4. 部署脚本

#### 4.1 Windows 快速启动
- **文件**: `deploy.bat`
- **功能**: 
  - 自动检查 .env 文件
  - 检查 Docker 环境
  - 构建并启动所有服务
  - 可选运行验证脚本

#### 4.2 Linux/macOS 快速启动
- **文件**: `deploy.sh`
- **功能**: 同 deploy.bat

#### 4.3 部署验证脚本
- **Bash 版本**: `scripts/verify_nginx.sh`
- **PowerShell 版本**: `scripts/verify_nginx.ps1`
- **功能**:
  - 测试前端页面可访问性
  - 测试后端健康检查
  - 测试 API 文档
  - 检查 CORS 配置
  - 验证所有容器状态

### 5. 文档更新

#### 5.1 部署指南
- **文件**: `DEPLOYMENT.md`
- **内容**:
  - 架构说明
  - 详细部署步骤
  - Nginx 配置详解
  - 安全建议（HTTPS、限流等）
  - 故障排查
  - 监控与维护
  - 性能优化建议

#### 5.2 README 更新
- **文件**: `README.md`
- **更新内容**:
  - 添加 Nginx 架构说明
  - 更新访问地址（统一为 80 端口）
  - 添加验证脚本使用说明
  - 更新环境变量说明

## 🏗️ 架构对比

### 修改前（存在跨域问题）

```
浏览器 (http://localhost:3000)
    ↓ [跨域请求] ❌
后端 API (http://localhost:8000)
```

**问题**: 
- 需要配置 CORS
- 两个不同的端口
- 浏览器可能阻止跨域请求

### 修改后（无跨域问题）

```
浏览器 (http://localhost/)
    ↓
Nginx (http://localhost:80)
    ├─ /          → 前端 (frontend:3000)
    └─ /api/      → 后端 (backend:8000/api/)
```

**优势**:
- ✅ 无跨域问题（同一域名）
- ✅ 统一入口（只需开放 80 端口）
- ✅ 后端不直接暴露在公网
- ✅ 可以添加 HTTPS、限流、缓存等

## 🚀 使用方法

### 快速部署（Windows）

```bash
# 1. 双击运行或在命令行执行
deploy.bat

# 2. 按提示编辑 .env 文件

# 3. 选择是否运行验证脚本
```

### 快速部署（Linux/macOS）

```bash
# 1. 添加执行权限
chmod +x deploy.sh

# 2. 运行脚本
./deploy.sh

# 3. 按提示编辑 .env 文件

# 4. 选择是否运行验证脚本
```

### 手动部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 2. 构建并启动
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 3. 验证部署
bash scripts/verify_nginx.sh        # Linux/macOS
.\scripts\verify_nginx.ps1          # Windows PowerShell
```

## 📊 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端页面 | http://localhost/ | Next.js 应用 |
| 后端 API | http://localhost/api/ | FastAPI 服务 |
| 健康检查 | http://localhost/api/health | 服务状态 |
| API 文档 | http://localhost/api/docs | Swagger UI |

## 🔒 安全增强建议

### 1. 启用 HTTPS（强烈推荐）

如果使用域名，请配置 SSL 证书：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... 其他配置
}
```

### 2. 禁用 API 文档（生产环境）

在 `nginx.conf` 中注释掉：

```nginx
# location /api/docs { ... }
# location /api/openapi.json { ... }
```

### 3. 添加限流

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    # ... 其他配置
}
```

## 🛠️ 故障排查

### 常见问题

1. **502 Bad Gateway**
   - 检查后端/前端容器是否运行
   - 查看日志: `docker logs falcon-backend`

2. **跨域问题仍然存在**
   - 确认前端已重新构建
   - 清除浏览器缓存
   - 检查 `NEXT_PUBLIC_API_BASE_URL=/api` 已正确设置（仅生产环境）

3. **上传文件失败**
   - 检查 Nginx 的 `client_max_body_size`
   - 检查后端的 `MAX_UPLOAD_MB`
   - 两者必须保持一致

### 日志查看

```bash
# Nginx 日志
docker logs falcon-nginx
docker exec falcon-nginx tail -f /var/log/nginx/access.log
docker exec falcon-nginx tail -f /var/log/nginx/error.log

# 后端日志
docker logs -f falcon-backend

# 前端日志
docker logs -f falcon-frontend
```

## 📝 注意事项

1. **开发环境 vs 生产环境**
   - 开发环境：仍可使用独立端口，方便调试
   - 生产环境：使用 Nginx 统一入口

2. **端口冲突**
   - 确保宿主机 80 端口未被占用
   - 如需修改，调整 `NGINX_PORT` 环境变量

3. **数据持久化**
   - 数据库数据已通过 Docker Volume 持久化
   - 上传的文件存储在 `backend-storage` volume 中

4. **备份策略**
   ```bash
   # 备份数据库
   docker exec falcon-postgres pg_dump -U falcon falcon > backup.sql
   
   # 备份存储文件
   docker run --rm -v backend-storage:/data -v $(pwd):/backup alpine \
     tar czf /backup/storage_backup.tar.gz /data
   ```

## ✅ 验证清单

部署完成后，请逐项验证：

- [ ] 所有容器正常运行 (`docker compose ps`)
- [ ] 前端页面可访问 (http://localhost/)
- [ ] 后端 API 可访问 (http://localhost/api/health)
- [ ] 无跨域错误（浏览器控制台检查）
- [ ] 文件上传功能正常
- [ ] AI 功能正常（如果配置了 LLM）
- [ ] 数据库连接正常
- [ ] Redis 连接正常
- [ ] 运行验证脚本全部通过

## 🎯 下一步优化建议

1. **监控告警**
   - 集成 Prometheus + Grafana
   - 配置服务健康监控

2. **日志聚合**
   - 使用 ELK Stack 或 Loki
   - 集中管理所有服务日志

3. **自动化部署**
   - 配置 CI/CD 流水线
   - 自动化测试和部署

4. **高可用**
   - 多实例部署
   - 负载均衡
   - 故障自动转移

---

**实施日期**: 2026-04-21  
**实施人员**: AI Assistant  
**审核状态**: 待审核
