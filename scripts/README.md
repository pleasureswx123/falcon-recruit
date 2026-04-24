# 部署脚本使用说明

## 📋 概述

本目录包含 Falcon Recruit 项目的一键部署脚本，支持从本地开发机直接部署到远程服务器。

## 🔧 脚本列表

### 1. deploy-to-server.sh (Linux/macOS)
**功能**: 一键部署到远程服务器
**用法**: `bash scripts/deploy-to-server.sh`

### 2. deploy-to-server.ps1 (Windows)
**功能**: 一键部署到远程服务器（PowerShell 版本）
**用法**: `powershell -ExecutionPolicy Bypass -File scripts\deploy-to-server.ps1`

### 3. server-init.sh
**功能**: 检查服务器环境是否满足部署要求
**用法**: `bash scripts/server-init.sh`

### 4. rollback.sh
**功能**: 回滚部署，停止并清理服务
**用法**: `bash scripts/rollback.sh`

### 5. deploy.sh (增强版)
**功能**: 本地部署脚本（已增强健康检查和项目名称支持）
**用法**: `bash deploy.sh`

## 🚀 快速开始

### 首次部署流程

1. **检查服务器环境**
   ```bash
   bash scripts/server-init.sh
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，至少修改 POSTGRES_PASSWORD
   ```

3. **执行部署**
   ```bash
   # Linux/macOS
   bash scripts/deploy-to-server.sh
   
   # Windows
   powershell -ExecutionPolicy Bypass -File scripts\deploy-to-server.ps1
   ```

### 后续迭代部署

代码修改后，直接运行部署脚本即可：

```bash
bash scripts/deploy-to-server.sh
```

脚本会自动：
- 同步最新代码到服务器
- 重新构建 Docker 镜像
- 重启服务
- 验证部署结果

## ⚙️ 配置说明

### 服务器配置

在脚本中修改以下变量以适配你的服务器：

```bash
SERVER="root@192.168.10.130"      # 服务器地址
REMOTE_DIR="/opt/falcon-recruit"   # 远程部署目录
PROJECT_NAME="falcon-recruit"      # Docker Compose 项目名称
SSH_PASSWORD="lbt@123.com"         # SSH 密码
```

### 端口配置

默认使用 8080 端口，如需修改：

1. 编辑 `.env` 文件
2. 修改 `NGINX_PORT=8080` 为其他端口
3. 确保该端口未被占用

## 🔍 常见问题

### 1. 权限问题

**Linux/macOS**:
```bash
chmod +x scripts/*.sh
```

**Windows**:
如果遇到执行策略限制：
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2. SSH 连接失败

- 确认服务器 IP 和凭据正确
- 确认 SSH 服务正在运行
- 检查防火墙设置

### 3. 端口冲突

如果 8080 端口被占用：
1. 修改 `.env` 中的 `NGINX_PORT`
2. 重新运行部署脚本

### 4. 部署失败

使用回滚脚本清理：
```bash
bash scripts/rollback.sh
```

然后检查日志排查问题：
```bash
ssh root@192.168.10.130 'docker logs falcon-backend'
```

## 📊 管理命令

### 查看服务状态
```bash
ssh root@192.168.10.130 'cd /opt/falcon-recruit && docker compose -p falcon-recruit ps'
```

### 查看日志
```bash
# Nginx 日志
ssh root@192.168.10.130 'docker logs falcon-nginx'

# 后端日志
ssh root@192.168.10.130 'docker logs falcon-backend'

# 前端日志
ssh root@192.168.10.130 'docker logs falcon-frontend'

# 实时查看日志
ssh root@192.168.10.130 'docker logs -f falcon-backend'
```

### 停止服务
```bash
ssh root@192.168.10.130 'cd /opt/falcon-recruit && docker compose -p falcon-recruit down'
```

### 重启服务
```bash
ssh root@192.168.10.130 'cd /opt/falcon-recruit && docker compose -p falcon-recruit restart'
```

### 完全清除（包括数据）
```bash
ssh root@192.168.10.130 'cd /opt/falcon-recruit && docker compose -p falcon-recruit down -v'
```

## 🔒 安全建议

1. **修改默认密码**: 首次部署后立即修改 POSTGRES_PASSWORD
2. **配置防火墙**: 仅开放必要的端口（如 8080）
3. **定期备份**: 备份数据库和上传文件
4. **更新依赖**: 定期更新 Docker 镜像和依赖包

## 📝 注意事项

- 脚本使用 `sshpass` 进行 SSH 认证，生产环境建议使用 SSH 密钥
- 首次部署需要配置 .env 文件
- 数据通过 Docker Volume 持久化，删除容器不会丢失数据
- 现有服务器上的其他服务不受影响

## 🆘 技术支持

如有问题，请查看：
- [DEPLOYMENT.md](../DEPLOYMENT.md) - 详细部署文档
- 项目 README
- 联系开发团队
