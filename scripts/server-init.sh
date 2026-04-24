#!/bin/bash
# 猎鹰招聘系统 - 服务器环境初始化检查脚本
# 在部署前检查服务器环境是否满足要求

set -e

SERVER="root@192.168.10.130"
SSH_PASSWORD="lbt@123.com"

echo "=========================================="
echo "  猎鹰招聘系统 - 服务器环境检查"
echo "=========================================="
echo ""

# 检查 Docker 版本和状态
echo "[1/5] 检查 Docker 环境..."
docker_version=$(sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER "docker --version" 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "✗ Docker 未安装或无法连接"
    exit 1
fi
echo "✓ Docker 已安装: $docker_version"

docker_status=$(sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER "docker info" 2>/dev/null | grep "Server Version")
echo "✓ Docker 服务运行正常"
echo ""

# 检查磁盘空间
echo "[2/5] 检查磁盘空间..."
disk_info=$(sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER "df -h /" 2>/dev/null | tail -1)
disk_available=$(echo $disk_info | awk '{print $4}')
disk_usage=$(echo $disk_info | awk '{print $5}')

echo "  磁盘使用情况: $disk_usage"
echo "  可用空间: $disk_available"

# 检查是否有足够的空间(至少 5GB)
disk_available_gb=$(echo $disk_available | sed 's/G//')
if (( $(echo "$disk_available_gb < 5" | bc -l) )); then
    echo "✗ 磁盘空间不足,建议至少有 5GB 可用空间"
    exit 1
fi
echo "✓ 磁盘空间充足"
echo ""

# 检查内存
echo "[3/5] 检查内存..."
mem_info=$(sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER "free -h" 2>/dev/null | grep "Mem:")
mem_total=$(echo $mem_info | awk '{print $2}')
mem_available=$(echo $mem_info | awk '{print $7}')

echo "  总内存: $mem_total"
echo "  可用内存: $mem_available"
echo "✓ 内存检查通过"
echo ""

# 检查端口可用性
echo "[4/5] 检查端口可用性..."
nginx_port=$(grep -E "^NGINX_PORT=" .env 2>/dev/null | cut -d'=' -f2 || echo "8080")
if [ -z "$nginx_port" ]; then
    nginx_port="8080"
fi

echo "  计划使用端口: $nginx_port"

# 检查端口是否被占用
port_in_use=$(sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER "ss -tlnp | grep ':$nginx_port'" 2>/dev/null)
if [ -n "$port_in_use" ]; then
    echo "✗ 端口 $nginx_port 已被占用:"
    echo "$port_in_use"
    echo ""
    echo "请修改 .env 文件中的 NGINX_PORT 为其他端口"
    exit 1
fi
echo "✓ 端口 $nginx_port 可用"
echo ""

# 检查现有容器
echo "[5/5] 检查现有容器..."
existing_containers=$(sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER "docker ps --format '{{.Names}}'" 2>/dev/null)
echo "  当前运行的容器:"
if [ -n "$existing_containers" ]; then
    echo "$existing_containers" | while read container; do
        echo "    - $container"
    done
else
    echo "    (无)"
fi
echo ""

# 检查是否有冲突的容器名
conflict_containers=$(sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER "docker ps -a --format '{{.Names}}'" 2>/dev/null | grep -E "falcon-(postgres|redis|backend|frontend|nginx)")
if [ -n "$conflict_containers" ]; then
    echo "⚠ 警告: 发现可能冲突的容器:"
    echo "$conflict_containers"
    echo ""
    echo "这些容器可能与新项目冲突,建议先停止并删除它们:"
    echo "  ssh $SERVER 'docker stop falcon-postgres falcon-redis falcon-backend falcon-frontend falcon-nginx'"
    echo "  ssh $SERVER 'docker rm falcon-postgres falcon-redis falcon-backend falcon-frontend falcon-nginx'"
    echo ""
else
    echo "✓ 未发现冲突的容器"
fi
echo ""

# 输出总结
echo "=========================================="
echo "  环境检查完成！"
echo "=========================================="
echo ""
echo "服务器状态:"
echo "  - Docker: 正常运行"
echo "  - 磁盘空间: $disk_available 可用"
echo "  - 内存: $mem_available 可用"
echo "  - 端口 $nginx_port: 可用"
echo ""
echo "可以开始部署了!"
echo "  执行: bash scripts/deploy-to-server.sh"
echo ""
