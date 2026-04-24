#!/bin/bash
# 猎鹰招聘系统 - 生产环境快速启动脚本 (Linux/macOS)
# 自动构建并启动所有服务（包含 Nginx）

set -e

# 项目名称(用于 docker compose -p)
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-falcon-recruit}

echo "=========================================="
echo "  猎鹰招聘系统 - 生产环境部署"
echo "=========================================="
echo ""

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "[警告] .env 文件不存在！"
    echo "正在从 .env.example 复制..."
    cp .env.example .env
    echo ""
    echo "[重要] 请编辑 .env 文件，配置以下内容："
    echo "  - POSTGRES_PASSWORD (数据库密码)"
    echo "  - OPENAI_API_KEY (LLM API 密钥，可选)"
    echo ""
    read -p "按回车键继续..."
    exit 1
fi

# 检查必要的配置项
POSTGRES_PASSWORD=$(grep -E "^POSTGRES_PASSWORD=" .env | cut -d'=' -f2)
if [ "$POSTGRES_PASSWORD" = "falcon_dev_pw" ] || [ -z "$POSTGRES_PASSWORD" ]; then
    echo "[警告] POSTGRES_PASSWORD 仍为默认值或未设置"
    echo "为了安全起见,建议修改为强密码"
    echo ""
    read -p "是否继续部署? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "部署已取消"
        exit 1
    fi
fi

echo "[1/3] 检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    echo "[错误] Docker 未安装"
    exit 1
fi
echo "✓ Docker 已安装"
echo ""

echo "[2/3] 构建并启动服务..."
docker compose -p $COMPOSE_PROJECT_NAME -f docker-compose.yml -f docker-compose.prod.yml up -d --build
if [ $? -ne 0 ]; then
    echo "[错误] 服务启动失败"
    exit 1
fi
echo "✓ 服务启动成功"
echo ""

# 添加函数：等待服务就绪
wait_for_service() {
    local service_name=$1
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker compose -p $COMPOSE_PROJECT_NAME ps $service_name | grep -q "Up"; then
            echo "✓ $service_name 已就绪"
            return 0
        fi
        echo "  等待 $service_name 启动... ($attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "✗ $service_name 启动超时"
    return 1
}

# 添加函数：健康检查
check_health() {
    local max_attempts=15
    local attempt=1
    local nginx_port=${NGINX_PORT:-8080}
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf http://localhost:$nginx_port/api/health > /dev/null 2>&1; then
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

echo "[3/3] 等待服务就绪..."
wait_for_service "nginx" && wait_for_service "backend" && wait_for_service "frontend"
check_health

echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端页面: http://localhost/"
echo "  后端 API: http://localhost/api/"
echo "  健康检查: http://localhost/api/health"
echo "  API 文档: http://localhost/api/docs"
echo ""
echo "查看服务状态:"
echo "  docker compose -p $COMPOSE_PROJECT_NAME -f docker-compose.yml -f docker-compose.prod.yml ps"
echo ""
echo "查看日志:"
echo "  docker logs falcon-nginx"
echo "  docker logs falcon-backend"
echo "  docker logs falcon-frontend"
echo ""
echo "停止服务:"
echo "  docker compose -p $COMPOSE_PROJECT_NAME -f docker-compose.yml -f docker-compose.prod.yml down"
echo ""

# 询问是否运行验证脚本
read -p "是否运行部署验证脚本？(y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    bash scripts/verify_nginx.sh
fi
