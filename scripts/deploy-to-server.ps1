# 猎鹰招聘系统 - Windows 远程服务器一键部署脚本 (PowerShell)
# 自动同步代码到远程服务器并部署

param(
    [string]$ServerHost = "192.168.10.130",
    [string]$ServerUser = "root",
    [string]$RemoteDir  = "/opt/falcon-recruit",
    [string]$ProjectName = "falcon-recruit"
)

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot | Split-Path -Parent
$TMP  = $env:TEMP

# 颜色输出函数
function Write-Step { param($msg) Write-Host "`n[INFO] $msg" -ForegroundColor Cyan }
function Write-OK   { param($msg) Write-Host "[ OK ] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "[ERR ] $msg" -ForegroundColor Red; Read-Host "按 Enter 退出"; exit 1 }

$SSH_TARGET = "${ServerUser}@${ServerHost}"
$SSH_OPTS   = @("-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10")

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "   猎鹰招聘系统 - 远程服务器部署" -ForegroundColor Cyan
Write-Host "   目标: ${ServerHost}:8080" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# -------------------------------------------------------
# Step 1: 检查本地工具
# -------------------------------------------------------
Write-Step "Step 1/5: 检查本地工具..."

$sshCmd = Get-Command ssh -ErrorAction SilentlyContinue
if (-not $sshCmd) { Write-Fail "未找到 ssh，请启用 Windows OpenSSH 客户端" }
Write-OK "SSH: $($sshCmd.Source)"

$tarCmd = Get-Command tar -ErrorAction SilentlyContinue
if (-not $tarCmd) { Write-Fail "未找到 tar，Windows 10 1903+ 已内置，请更新系统" }
Write-OK "tar: $($tarCmd.Source)"

$scpCmd = Get-Command scp -ErrorAction SilentlyContinue
if (-not $scpCmd) { Write-Fail "未找到 scp" }
Write-OK "scp OK"

# -------------------------------------------------------
# Step 2: 检查配置文件
# -------------------------------------------------------
Write-Step "Step 2/5: 检查配置文件..."

$envFile = Join-Path $ROOT ".env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $ROOT ".env.example") $envFile
    Write-Warn "已复制 .env.example -> .env"
    Write-Warn "请先编辑 .env 设置生产密码，然后重新运行！"
    Write-Host "  notepad .env" -ForegroundColor Yellow
    Read-Host "按 Enter 退出"
    exit 1
}
Write-OK ".env 存在"

# -------------------------------------------------------
# Step 3: 打包源码并上传到服务器 + 清理旧部署
# -------------------------------------------------------
Write-Step "Step 3/5: 打包源码..."

$zipFile = Join-Path $TMP "falcon_recruit_deploy.tar.gz"
if (Test-Path $zipFile) { Remove-Item $zipFile -Force }

& tar -czf $zipFile `
    --exclude=.git `
    --exclude=node_modules `
    --exclude=.next `
    --exclude=__pycache__ `
    --exclude=*.pyc `
    --exclude=.dockerignore `
    --exclude=*.swp `
    --exclude=*.swo `
    --exclude=.vscode `
    --exclude=.idea `
    --exclude=.env `
    -C $ROOT .

if ($LASTEXITCODE -ne 0) { Write-Fail "打包失败" }

$sizeMB = [math]::Round((Get-Item $zipFile).Length / 1MB, 1)
Write-OK "打包完成: $sizeMB MB"

Write-Step "上传到服务器 ${ServerHost}:${RemoteDir}..."
& scp @SSH_OPTS $zipFile "${SSH_TARGET}:/tmp/falcon_recruit_deploy.tar.gz"
if ($LASTEXITCODE -ne 0) { Write-Fail "上传失败，请检查网络和 SSH 权限" }
Write-OK "上传完成"

# 单独上传 .env 文件（因为被 .gitignore 排除）
Write-Step "上传配置文件 .env..."
$envFile = Join-Path $ROOT ".env"
& scp @SSH_OPTS $envFile "${SSH_TARGET}:/tmp/falcon_recruit.env"
if ($LASTEXITCODE -ne 0) { Write-Fail ".env 文件上传失败" }
Write-OK ".env 上传完成"

# -------------------------------------------------------
# Step 3.5: 清理服务器旧部署（确保环境干净）
# -------------------------------------------------------
Write-Step "Step 3.5/5: 清理服务器旧部署..."

Write-Host "  停止并移除旧容器..." -ForegroundColor Gray
& ssh @SSH_OPTS $SSH_TARGET "docker compose -p $ProjectName down 2>/dev/null || true"
Write-OK "旧容器已停止"

Write-Host "  清理旧代码目录..." -ForegroundColor Gray
& ssh @SSH_OPTS $SSH_TARGET "rm -rf ${RemoteDir} && mkdir -p ${RemoteDir}"
Write-OK "旧代码已清理"

# -------------------------------------------------------
# Step 4: 服务器端 - 解压 + 构建 + 启动
# -------------------------------------------------------
Write-Step "Step 4/5: 在服务器上解压并启动服务..."

Write-Host "  在服务器上执行部署命令..." -ForegroundColor Gray

# 直接在 SSH 会话中执行部署命令（使用单行避免换行符问题）
# 注意：tar 解压后会创建 falcon-recruit 子目录，需要进入该目录
# 重要：必须同时使用 docker-compose.yml 和 docker-compose.prod.yml
$deployCommands = "cd $RemoteDir && tar -xzf /tmp/falcon_recruit_deploy.tar.gz && cd falcon-recruit && mv /tmp/falcon_recruit.env .env && docker compose -p $ProjectName -f docker-compose.yml -f docker-compose.prod.yml up -d --build"

& ssh @SSH_OPTS $SSH_TARGET $deployCommands
if ($LASTEXITCODE -ne 0) { Write-Fail "服务器端部署失败，请检查日志" }

Write-OK "服务器端部署完成"

# -------------------------------------------------------
# Step 5: 验证部署
# -------------------------------------------------------
Write-Step "Step 5/5: 验证服务..."
Start-Sleep -Seconds 10

try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri "http://${ServerHost}:8080/api/health" -TimeoutSec 10 -ErrorAction Stop
    if ($resp.StatusCode -eq 200) { Write-OK "后端健康检查通过" }
} catch {
    Write-Warn "后端未响应，请检查: ssh $SSH_TARGET 'docker logs falcon-backend'"
}

# 清理本地临时文件
Remove-Item $zipFile -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "   部署完成！" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  [对外访问]" -ForegroundColor White
Write-Host "    前端页面:       http://${ServerHost}:8080/" -ForegroundColor Cyan
Write-Host "    后端 API:       http://${ServerHost}:8080/api/" -ForegroundColor Cyan
Write-Host "    健康检查:       http://${ServerHost}:8080/api/health" -ForegroundColor Cyan
Write-Host "    lbt-web 官网:   http://${ServerHost}:80        (未改动)" -ForegroundColor Gray
Write-Host ""
Write-Host "  [Docker 内部服务]  (仅容器间通信，不对外暴露)" -ForegroundColor White
Write-Host "    PostgreSQL:     postgres:5432     (数据库)" -ForegroundColor DarkCyan
Write-Host "    Redis:          redis:6379        (缓存/Session)" -ForegroundColor DarkCyan
Write-Host "    Backend:        backend:8000      (FastAPI 服务)" -ForegroundColor DarkCyan
Write-Host "    Frontend:       frontend:3000     (Next.js 应用)" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "  [常用运维命令]  (SSH 到服务器后执行)" -ForegroundColor White
Write-Host "    查看所有容器状态:" -ForegroundColor Gray
Write-Host "      docker compose -p $ProjectName ps" -ForegroundColor DarkGray
Write-Host "    实时查看日志:" -ForegroundColor Gray
Write-Host "      docker logs -f falcon-backend" -ForegroundColor DarkGray
Write-Host "      docker logs -f falcon-nginx" -ForegroundColor DarkGray
Write-Host "      docker logs -f falcon-frontend" -ForegroundColor DarkGray
Write-Host "    重启单个服务:" -ForegroundColor Gray
Write-Host "      docker compose -p $ProjectName restart backend" -ForegroundColor DarkGray
Write-Host "    停止所有服务:" -ForegroundColor Gray
Write-Host "      docker compose -p $ProjectName down" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  [下次部署]" -ForegroundColor White
Write-Host "    代码更新后，直接运行:" -ForegroundColor Gray
Write-Host '      .\scripts\deploy-to-server.ps1' -ForegroundColor DarkGray
Write-Host ""
