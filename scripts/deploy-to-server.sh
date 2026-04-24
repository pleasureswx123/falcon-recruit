#!/bin/bash
# 猎鹰招聘系统 - 远程服务器一键部署脚本 (Linux/macOS)
# 自动同步代码到远程服务器并部署

set -e

# ==================== 配置区域 ====================
SERVER="root@192.168.10.130"
REMOTE_DIR="/opt/falcon-recruit"
PROJECT_NAME="falcon-recruit"
SSH_PASSWORD="lbt@123.com"

# ==================== 函数定义 ====================

# 检查依赖工具
check_dependencies() {
    echo "[0/5] 检查依赖工具..."
    
    if ! command -v ssh &> /dev/null; then
        echo "[错误] SSH 客户端未安装"
        exit 1
    fi
    
    if ! command -v rsync &> /dev/null; then
        echo "[错误] rsync 未安装,请先安装: sudo apt-get install rsync (Ubuntu) 或 brew install rsync (macOS)"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        echo "[警告] curl 未安装,将无法验证部署结果"
    fi
    
    echo "✓ 依赖检查通过"
    echo ""
}

# 同步代码到服务器
sync_code() {
    echo "[1/5] 同步代码到服务器..."
    echo "  目标: $SERVER:$REMOTE_DIR"
    echo ""
    
    # 创建远程目录
    sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER "mkdir -p $REMOTE_DIR"
    
    # 同步文件(排除不必要的文件和目录)
    rsync -avz --delete \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='.next' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.dockerignore' \
        --exclude='*.swp' \
        --exclude='*.swo' \
        --exclude='.vscode' \
        --exclude='.idea' \
        --exclude='.env' \
        ./ $SERVER:$REMOTE_DIR/
    
    echo "✓ 代码同步完成"
    echo ""
}

# 远程执行部署
remote_deploy() {
    echo "[2/5] 远程构建并启动服务..."
    
    sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER << EOF
    set -e
    cd $REMOTE_DIR
    
    # 检查 .env 文件是否存在
    if [ ! -f ".env" ]; then
        echo "正在从 .env.example 复制配置文件..."
        cp .env.example .env
        echo ""
        echo "=========================================="
        echo "  首次部署提示"
        echo "=========================================="
        echo ""
        echo "重要: 请编辑 .env 文件,至少配置以下内容:"
        echo "  - POSTGRES_PASSWORD (数据库密码,必须修改为强密码)"
        echo "  - OPENAI_API_KEY (可选,LLM API 密钥)"
        echo ""
        echo "编辑命令: nano .env 或 vim .env"
        echo ""
        echo "配置完成后,请重新运行此部署脚本。"
        echo "=========================================="
        exit 1
    fi
    
    # 检查必要的配置项
    POSTGRES_PASSWORD=\$(grep -E "^POSTGRES_PASSWORD=" .env | cut -d'=' -f2)
    if [ "\$POSTGRES_PASSWORD" = "falcon_dev_pw" ] || [ -z "\$POSTGRES_PASSWORD" ]; then
        echo "[警告] POSTGRES_PASSWORD 仍为默认值或未设置"
        echo "为了安全起见,建议修改为强密码"
        echo ""
        read -p "是否继续部署? (y/n): " -n 1 -r
        echo ""
        if [[ ! \$REPLY =~ ^[Yy]$ ]]; then
            echo "部署已取消"
            exit 1
        fi
    fi
    
    # 停止旧的服务(如果存在)
    echo "检查是否有旧的服务在运行..."
    docker compose -p $PROJECT_NAME down 2>/dev/null || true
    
    # 构建并启动服务
    echo "开始构建 Docker 镜像..."
    docker compose -p $PROJECT_NAME -f docker-compose.yml -f docker-compose.prod.yml up -d --build
    
    echo "✓ 服务启动命令已执行"
EOF
    
    echo "✓ 远程部署命令执行完成"
    echo ""
}

# 等待服务就绪
wait_for_services() {
    echo "[3/5] 等待服务就绪..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        # 检查容器状态
        local container_status=$(sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER "docker compose -p $PROJECT_NAME ps" 2>/dev/null)
        
        if echo "$container_status" | grep -q "falcon-nginx.*Up" && \
           echo "$container_status" | grep -q "falcon-backend.*Up" && \
           echo "$container_status" | grep -q "falcon-frontend.*Up"; then
            echo "✓ 所有容器已启动"
            return 0
        fi
        
        echo "  等待服务启动... ($attempt/$max_attempts)"
        sleep 3
        attempt=$((attempt + 1))
    done
    
    echo "✗ 服务启动超时,请检查日志"
    echo "查看日志: ssh $SERVER 'docker logs falcon-nginx'"
    return 1
}

# 验证部署结果
verify_deployment() {
    echo "[4/5] 验证部署结果..."
    
    # 获取 Nginx 端口
    local nginx_port=$(grep -E "^NGINX_PORT=" .env 2>/dev/null | cut -d'=' -f2 || echo "8080")
    if [ -z "$nginx_port" ]; then
        nginx_port="8080"
    fi
    
    echo "  检查 http://192.168.10.130:$nginx_port/api/health"
    
    local max_attempts=15
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf http://192.168.10.130:$nginx_port/api/health > /dev/null 2>&1; then
            echo "✓ 后端健康检查通过"
            return 0
        fi
        echo "  等待后端服务就绪... ($attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "✗ 后端健康检查失败"
    return 1
}

# 显示部署结果
show_result() {
    echo ""
    echo "[5/5] 生成部署报告..."
    echo ""
    
    local nginx_port=$(grep -E "^NGINX_PORT=" .env 2>/dev/null | cut -d'=' -f2 || echo "8080")
    if [ -z "$nginx_port" ]; then
        nginx_port="8080"
    fi
    
    echo "=========================================="
    echo "  部署完成！"
    echo "=========================================="
    echo ""
    echo "访问地址:"
    echo "  前端页面: http://192.168.10.130:$nginx_port/"
    echo "  后端 API: http://192.168.10.130:$nginx_port/api/"
    echo "  健康检查: http://192.168.10.130:$nginx_port/api/health"
    echo ""
    echo "管理命令:"
    echo "  # 查看服务状态"
    echo "  sshpass -p '$SSH_PASSWORD' ssh $SERVER 'cd $REMOTE_DIR && docker compose -p $PROJECT_NAME ps'"
    echo ""
    echo "  # 查看日志"
    echo "  sshpass -p '$SSH_PASSWORD' ssh $SERVER 'docker logs falcon-nginx'"
    echo "  sshpass -p '$SSH_PASSWORD' ssh $SERVER 'docker logs falcon-backend'"
    echo "  sshpass -p '$SSH_PASSWORD' ssh $SERVER 'docker logs falcon-frontend'"
    echo ""
    echo "  # 实时查看日志"
    echo "  sshpass -p '$SSH_PASSWORD' ssh $SERVER 'docker logs -f falcon-backend'"
    echo ""
    echo "  # 停止服务"
    echo "  sshpass -p '$SSH_PASSWORD' ssh $SERVER 'cd $REMOTE_DIR && docker compose -p $PROJECT_NAME down'"
    echo ""
    echo "  # 重启服务"
    echo "  sshpass -p '$SSH_PASSWORD' ssh $SERVER 'cd $REMOTE_DIR && docker compose -p $PROJECT_NAME restart'"
    echo ""
    echo "  # 更新部署(代码修改后)"
    echo "  bash scripts/deploy-to-server.sh"
    echo ""
    echo "注意事项:"
    echo "  - 数据持久化: 数据库和上传文件已通过 Docker Volume 持久化"
    echo "  - 备份建议: 定期备份数据库和存储文件"
    echo "  - 安全提示: 请确保防火墙仅开放必要端口($nginx_port)"
    echo ""
}

# ==================== 主流程 ====================

echo "=========================================="
echo "  猎鹰招聘系统 - 远程服务器部署"
echo "=========================================="
echo ""

# 检查依赖
check_dependencies

# 同步代码
sync_code

# 远程部署
remote_deploy

# 等待服务
wait_for_services

# 验证部署
if verify_deployment; then
    show_result
else
    echo ""
    echo "=========================================="
    echo "  部署可能存在问题"
    echo "=========================================="
    echo ""
    echo "请检查服务状态:"
    echo "  sshpass -p '$SSH_PASSWORD' ssh $SERVER 'cd $REMOTE_DIR && docker compose -p $PROJECT_NAME ps'"
    echo ""
    echo "查看日志排查问题:"
    echo "  sshpass -p '$SSH_PASSWORD' ssh $SERVER 'docker logs falcon-backend'"
    echo ""
    exit 1
fi
