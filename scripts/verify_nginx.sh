#!/bin/bash
# 猎鹰招聘系统 - Nginx 部署验证脚本
# 用于验证生产环境部署是否正确

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
BASE_URL="${1:-http://localhost}"

echo "=========================================="
echo "  猎鹰招聘系统 - 部署验证"
echo "=========================================="
echo ""
echo "测试地址: $BASE_URL"
echo ""

# 计数器
PASS=0
FAIL=0

# 测试函数
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "测试 $name ... "
    
    # 发送请求并获取状态码
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $status_code)"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (期望: HTTP $expected_status, 实际: HTTP $status_code)"
        ((FAIL++))
        return 1
    fi
}

# 1. 测试前端页面
test_endpoint "前端页面" "$BASE_URL/" 200

# 2. 测试后端健康检查
test_endpoint "健康检查" "$BASE_URL/api/health" 200

# 3. 测试 API 文档（如果启用）
echo -n "测试 API 文档 ... "
status_code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/docs" 2>/dev/null || echo "000")
if [ "$status_code" = "200" ] || [ "$status_code" = "401" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $status_code)"
    ((PASS++))
else
    echo -e "${YELLOW}⚠ SKIP${NC} (HTTP $status_code - 可能已禁用)"
fi

# 4. 测试 CORS 头
echo -n "测试 CORS 配置 ... "
cors_header=$(curl -s -I -H "Origin: http://test.com" "$BASE_URL/api/health" 2>/dev/null | grep -i "access-control" || echo "")
if [ -n "$cors_header" ]; then
    echo -e "${GREEN}✓ PASS${NC} (CORS 头已配置)"
    ((PASS++))
else
    echo -e "${YELLOW}⚠ INFO${NC} (通过 Nginx 统一入口，无需 CORS)"
fi

# 5. 测试容器状态
echo ""
echo "检查容器状态..."
if command -v docker &> /dev/null; then
    containers=("falcon-nginx" "falcon-backend" "falcon-frontend" "falcon-postgres" "falcon-redis")
    for container in "${containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            echo -e "  ${GREEN}✓${NC} $container 运行中"
            ((PASS++))
        else
            echo -e "  ${RED}✗${NC} $container 未运行"
            ((FAIL++))
        fi
    done
else
    echo -e "  ${YELLOW}⚠${NC} Docker 未安装，跳过容器检查"
fi

# 总结
echo ""
echo "=========================================="
echo "  测试结果汇总"
echo "=========================================="
echo -e "通过: ${GREEN}$PASS${NC}"
echo -e "失败: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！部署成功！${NC}"
    exit 0
else
    echo -e "${RED}✗ 存在失败的测试，请检查部署配置${NC}"
    exit 1
fi
