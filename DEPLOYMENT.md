# 生产环境部署指南 - Nginx 反向代理方案

## 📋 概述

本方案通过在生产环境中添加 Nginx 作为反向代理，彻底解决前后端跨域问题。所有请求都通过统一的域名和端口访问，Nginx 负责将请求路由到对应的前端或后端服务。

## 🏗️ 架构说明

```
用户浏览器
    ↓
http://your-domain.com:80 (Nginx)
    ↓
    ├─ /          → 前端 Next.js 应用 (container: frontend:3000)
    └─ /api/      → 后端 FastAPI 服务 (container: backend:8000)
```

### 核心优势

1. **彻底解决跨域**：前后端在同一域名下，浏览器不会触发 CORS 限制
2. **统一入口**：只需暴露一个端口（80），简化防火墙配置
3. **安全性提升**：后端服务不直接暴露在公网
4. **性能优化**：Nginx 可以处理静态资源缓存、负载均衡等

## 🚀 部署步骤

### 1. 准备环境变量

复制并编辑 `.env` 文件：

```bash
cp .env.example .env
```

关键配置项：

```env
# Nginx 对外端口（默认 80）
NGINX_PORT=80

# 前端构建时使用相对路径
NEXT_PUBLIC_API_BASE_URL=/api

# CORS 配置（通过 Nginx 统一入口后可设为 *）
CORS_ORIGINS=*

# 数据库密码（生产环境必须修改为强密码）
POSTGRES_PASSWORD=your_strong_password_here

# API Key（生产环境必填）
FALCON_API_KEY=your_api_key_here

# LLM 配置（可选）
OPENAI_API_KEY=your_llm_key
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
LLM_MODEL=doubao-1-5-pro-32k-250115
```

### 2. 构建并启动服务

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 3. 验证部署

```bash
# 查看所有容器状态
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# 查看 Nginx 日志
docker logs falcon-nginx

# 测试访问
curl http://localhost/              # 应该返回前端页面
curl http://localhost/api/health    # 应该返回后端健康检查响应
curl http://localhost/api/docs      # API 文档（如果启用）
```

### 4. 访问应用

- **前端页面**: http://your-server-ip/
- **后端 API**: http://your-server-ip/api/
- **健康检查**: http://your-server-ip/api/health
- **API 文档**: http://your-server-ip/api/docs

## 🔧 Nginx 配置详解

### 配置文件位置

- 主配置: `nginx.conf`
- Dockerfile: `Dockerfile.nginx`

### 关键配置说明

#### 1. 前端代理

```nginx
location / {
    proxy_pass http://frontend:3000;
    # WebSocket 支持
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    # 超时设置
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}
```

#### 2. 后端 API 代理

```nginx
location /api/ {
    proxy_pass http://backend:8000/api/;
    # AI 处理可能需要较长时间
    proxy_connect_timeout 120s;
    proxy_send_timeout 120s;
    proxy_read_timeout 120s;
    # 禁用缓冲以支持流式响应
    proxy_buffering off;
    proxy_request_buffering off;
}
```

#### 3. 上传大小限制

```nginx
client_max_body_size 200m;  # 与后端 MAX_UPLOAD_MB 保持一致
```

## 🔒 安全建议

### 1. HTTPS 配置（推荐）

如果使用域名，强烈建议配置 HTTPS。创建 `nginx-ssl.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # SSL 优化配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # ... 其他配置同上
}

# HTTP 自动跳转 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

在 `docker-compose.prod.yml` 中挂载证书：

```yaml
nginx:
  volumes:
    - ./nginx-ssl.conf:/etc/nginx/conf.d/default.conf
    - ./ssl:/etc/nginx/ssl:ro
```

### 2. 禁用 API 文档（生产环境）

在 `nginx.conf` 中注释掉文档相关配置：

```nginx
# location /docs {
#     proxy_pass http://backend:8000/docs;
# }

# location /openapi.json {
#     proxy_pass http://backend:8000/openapi.json;
# }
```

### 3. 限流配置

在 `nginx.conf` 的 `http` 块中添加：

```nginx
http {
    # 限制 API 请求频率
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    
    server {
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            # ... 其他配置
        }
    }
}
```

## 🛠️ 故障排查

### 1. 容器启动失败

```bash
# 查看特定容器日志
docker logs falcon-nginx
docker logs falcon-backend
docker logs falcon-frontend

# 检查容器状态
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

### 2. 502 Bad Gateway

可能原因：
- 后端/前端服务未启动
- 网络连接问题

解决方法：

```bash
# 重启所有服务
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart

# 检查服务间网络
docker network inspect falcon-recruit_falcon-net
```

### 3. 跨域问题仍然存在

检查点：
1. 确认 `NEXT_PUBLIC_API_BASE_URL=/api` 已正确设置
2. 确认前端重新构建（清除缓存）
3. 检查浏览器控制台的网络请求地址

```bash
# 强制重新构建
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build --force-recreate
```

### 4. 上传文件失败

检查：
1. Nginx 的 `client_max_body_size` 设置
2. 后端的 `MAX_UPLOAD_MB` 配置
3. 两者必须保持一致

## 📊 监控与维护

### 日志查看

```bash
# Nginx 访问日志
docker exec falcon-nginx tail -f /var/log/nginx/access.log

# Nginx 错误日志
docker exec falcon-nginx tail -f /var/log/nginx/error.log

# 后端日志
docker logs -f falcon-backend

# 前端日志
docker logs -f falcon-frontend
```

### 性能优化

1. **启用 Gzip 压缩**

在 `nginx.conf` 的 `server` 块外添加：

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
```

2. **静态资源缓存**

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    proxy_pass http://frontend:3000;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

## 🔄 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 清理旧镜像
docker image prune -f
```

## ✅ 验证清单

部署完成后，请逐项验证：

- [ ] 所有容器正常运行 (`docker compose ps`)
- [ ] 前端页面可访问 (http://your-server-ip/)
- [ ] 后端 API 可访问 (http://your-server-ip/api/health)
- [ ] 无跨域错误（浏览器控制台检查）
- [ ] 文件上传功能正常
- [ ] AI 功能正常（如果配置了 LLM）
- [ ] 数据库连接正常
- [ ] Redis 连接正常

## 📝 注意事项

1. **开发环境 vs 生产环境**
   - 开发环境：前后端独立运行，需要配置 CORS
   - 生产环境：通过 Nginx 统一入口，无跨域问题

2. **端口冲突**
   - 确保宿主机 80 端口未被占用
   - 如需修改，调整 `NGINX_PORT` 环境变量

3. **数据持久化**
   - 数据库数据已通过 Docker Volume 持久化
   - 上传的文件存储在 `backend-storage` volume 中

4. **备份策略**
   ```bash
   # 备份数据库
   docker exec falcon-postgres pg_dump -U falcon falcon > backup_$(date +%Y%m%d).sql
   
   # 备份存储文件
   docker run --rm -v falcon-recruit_backend-storage:/data -v $(pwd):/backup alpine tar czf /backup/storage_backup.tar.gz /data
   ```

5. **API 路径规范**
   - 所有后端 API 端点都以 `/api/` 开头
   - 例如：`/api/jobs`, `/api/candidates`, `/api/tasks`
   - 健康检查：`/api/health`
   - API 文档：`/api/docs`

## ✅ 验证清单

部署完成后，请逐项验证：

- [ ] 所有容器正常运行 (`docker compose ps`)
- [ ] 前端页面可访问 (http://your-server-ip/)
- [ ] 后端 API 可访问 (http://your-server-ip/api/health)
- [ ] 无跨域错误（浏览器控制台检查）
- [ ] 文件上传功能正常
- [ ] AI 功能正常（如果配置了 LLM）
- [ ] 数据库连接正常
- [ ] Redis 连接正常

---

**技术支持**: 如有问题，请查看项目文档或联系开发团队。
