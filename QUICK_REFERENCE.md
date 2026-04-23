# Nginx 反向代理 - 快速参考卡

## 🎯 核心价值

**彻底解决跨域问题**：前后端通过同一域名访问，浏览器不再阻止请求。

## 📁 新增文件清单

```
falcon-recruit/
├── nginx.conf                          # Nginx 配置文件
├── Dockerfile.nginx                    # Nginx 容器构建文件
├── DEPLOYMENT.md                       # 详细部署指南
├── NGINX_IMPLEMENTATION_SUMMARY.md     # 实施总结文档
├── deploy.bat                          # Windows 快速启动脚本
├── deploy.sh                           # Linux/macOS 快速启动脚本
└── scripts/
    ├── verify_nginx.sh                 # Bash 验证脚本
    └── verify_nginx.ps1                # PowerShell 验证脚本
```

## 🔧 修改文件清单

```
docker-compose.prod.yml    # 添加 nginx 服务，调整前后端配置
.env.example               # 添加 NGINX_PORT 等变量
README.md                  # 更新部署说明
```

## 🚀 一键部署

### Windows
```bash
deploy.bat
```

### Linux/macOS
```bash
chmod +x deploy.sh
./deploy.sh
```

## 🔍 验证部署

### Windows
```powershell
.\scripts\verify_nginx.ps1
```

### Linux/macOS
```bash
bash scripts/verify_nginx.sh
```

## 🌐 访问地址

| 服务 | URL |
|------|-----|
| 前端 | http://localhost/ |
| API | http://localhost/api/ |
| 健康检查 | http://localhost/api/health |
| API 文档 | http://localhost/api/docs |

## 📊 架构示意

```
用户浏览器
    ↓
http://localhost:80 (Nginx)
    ├─ /          → frontend:3000
    └─ /api/      → backend:8000/api/
```

## ⚙️ 关键配置

### 环境变量 (.env)
```env
NGINX_PORT=80
NEXT_PUBLIC_API_BASE_URL=/api
CORS_ORIGINS=*
```

### Nginx 路由规则
- `/` → 前端 Next.js
- `/api/*` → 后端 FastAPI
- 上传限制: 200MB
- 超时: 前端 60s, 后端 120s

## 🛠️ 常用命令

```bash
# 启动服务
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 查看状态
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# 查看日志
docker logs falcon-nginx
docker logs falcon-backend
docker logs falcon-frontend

# 重启服务
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart

# 停止服务
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# 重新构建
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build --force-recreate
```

## 🔒 安全建议

1. **启用 HTTPS**（生产环境必需）
2. **禁用 API 文档**（`/api/docs`, `/api/openapi.json`）
3. **配置限流**（防止 DDoS）
4. **修改默认端口**（避免扫描）
5. **设置强密码**（数据库、API Key）

## 🐛 故障排查

### 502 Bad Gateway
```bash
# 检查后端是否运行
docker ps | grep falcon-backend

# 查看后端日志
docker logs falcon-backend

# 重启后端
docker restart falcon-backend
```

### 跨域问题仍存在
```bash
# 强制重新构建前端
docker compose -f docker-compose.yml -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d frontend

# 清除浏览器缓存
```

### 上传失败
```bash
# 检查 Nginx 配置
grep client_max_body_size nginx.conf

# 检查后端配置
grep MAX_UPLOAD_MB .env

# 两者必须一致（默认 200MB）
```

## 📚 详细文档

- **部署指南**: `DEPLOYMENT.md`
- **实施总结**: `NGINX_IMPLEMENTATION_SUMMARY.md`
- **项目文档**: `docs/PRD.md`, `docs/TDD.md`

## 💡 提示

- ✅ 开发环境仍可独立运行前后端
- ✅ 生产环境推荐使用 Nginx 统一入口
- ✅ 所有 API 路径以 `/api/` 开头
- ✅ 定期备份数据库和存储文件
- ✅ 监控服务日志和性能指标

---

**最后更新**: 2026-04-21  
**维护人员**: 开发团队
