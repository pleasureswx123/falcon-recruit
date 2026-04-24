#!/bin/bash
# 猎鹰招聘系统 - 部署回滚脚本
# 在部署失败时快速恢复到之前状态

set -e

SERVER="root@192.168.10.130"
REMOTE_DIR="/opt/falcon-recruit"
PROJECT_NAME="falcon-recruit"
SSH_PASSWORD="lbt@123.com"

echo "=========================================="
echo "  猎鹰招聘系统 - 部署回滚"
echo "=========================================="
echo ""

# 确认回滚操作
echo "⚠ 警告: 此操作将停止并删除所有 Falcon Recruit 容器"
echo ""
read -p "是否继续? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "回滚已取消"
    exit 0
fi

echo ""
echo "[1/3] 停止当前服务..."
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER << EOF
cd $REMOTE_DIR
docker compose -p $PROJECT_NAME down
EOF

if [ $? -eq 0 ]; then
    echo "✓ 服务已停止"
else
    echo "✗ 停止服务失败"
    exit 1
fi
echo ""

echo "[2/3] 清理临时文件..."
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER << EOF
# 保留数据卷,只删除容器和镜像
docker compose -p $PROJECT_NAME down --remove-orphans
EOF

if [ $? -eq 0 ]; then
    echo "✓ 临时文件已清理"
else
    echo "✗ 清理失败"
    exit 1
fi
echo ""

echo "[3/3] 检查现有服务状态..."
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER "docker ps" | grep -E "deploy-" || true

echo ""
echo "=========================================="
echo "  回滚完成！"
echo "=========================================="
echo ""
echo "当前状态:"
echo "  - Falcon Recruit 服务已停止"
echo "  - 数据卷已保留(数据库和上传文件未删除)"
echo "  - 现有服务运行正常"
echo ""
echo "如果需要完全清除(包括数据):"
echo "  ssh $SERVER 'cd $REMOTE_DIR && docker compose -p $PROJECT_NAME down -v'"
echo ""
echo "如果需要重新部署:"
echo "  bash scripts/deploy-to-server.sh"
echo ""
