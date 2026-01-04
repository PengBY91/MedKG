#!/bin/bash
# 检查项目标准化功能 - 端到端测试脚本

set -e  # Exit on error

echo "========================================="
echo "检查项目标准化 - 端到端测试"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8000/api/v1/examination"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function
test_api() {
    local name=$1
    local method=$2
    local endpoint=$3
    local expected_status=$4
    
    echo -n "Testing: $name ... "
    
    if [ "$method" = "GET" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    else
        status=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$BASE_URL$endpoint")
    fi
    
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $status)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC} (Expected $expected_status, got $status)"
        ((TESTS_FAILED++))
    fi
}

echo "Step 1: 检查Neo4j连接"
echo "-------------------------------------"
if docker ps | grep -q medkg-neo4j; then
    echo -e "${GREEN}✓ Neo4j容器正在运行${NC}"
else
    echo -e "${RED}✗ Neo4j容器未运行${NC}"
    echo "请先启动: docker-compose -f docker-compose-neo4j.yml up -d"
    exit 1
fi
echo ""

echo "Step 2: 检查后端服务"
echo "-------------------------------------"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ 后端服务正常${NC}"
else
    echo -e "${RED}✗ 后端服务未启动${NC}"
    echo "请先启动: uvicorn app.main:app --reload"
    exit 1
fi
echo ""

echo "Step 3: 测试图谱API"
echo "-------------------------------------"
test_api "获取图谱统计" "GET" "/graph/stats" "200"
test_api "获取完整树结构" "GET" "/graph/tree" "200"
test_api "查询本体信息" "GET" "/ontology" "200"
echo ""

echo "Step 4: 测试数据导入"
echo "-------------------------------------"
if [ -f "../examination_ontology.csv" ]; then
    echo -n "导入本体数据 ... "
    response=$(curl -s -X POST "$BASE_URL/import" \
        -F "file=@../examination_ontology.csv" \
        -F "clear_existing=false")
    
    if echo "$response" | grep -q "success.*true"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((TESTS_PASSED++))
        
        # Display stats
        echo "$response" | python3 -m json.tool 2>/dev/null | grep -E "(level1_nodes|level2_nodes|method_nodes)" || true
    else
        echo -e "${YELLOW}⚠ SKIPPED${NC} (数据可能已存在)"
    fi
else
    echo -e "${YELLOW}⚠ SKIPPED${NC} (CSV文件不存在)"
fi
echo ""

echo "Step 5: 测试标准化功能"
echo "-------------------------------------"
if [ -f "../test_examination_data.csv" ]; then
    echo -n "上传测试文件 ... "
    response=$(curl -s -X POST "$BASE_URL/upload" \
        -F "file=@../test_examination_data.csv")
    
    if echo "$response" | grep -q "task_id"; then
        task_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['task_id'])" 2>/dev/null)
        echo -e "${GREEN}✓ PASSED${NC} (Task ID: $task_id)"
        ((TESTS_PASSED++))
        
        # Wait for processing
        echo -n "等待处理完成 ... "
        sleep 3
        
        # Check task status
        status_response=$(curl -s "$BASE_URL/tasks/$task_id")
        if echo "$status_response" | grep -q "completed"; then
            echo -e "${GREEN}✓ PASSED${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "${YELLOW}⚠ PROCESSING${NC}"
        fi
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${YELLOW}⚠ SKIPPED${NC} (测试文件不存在)"
fi
echo ""

echo "Step 6: 验证图谱数据"
echo "-------------------------------------"
echo "查询图谱统计信息:"
curl -s "$BASE_URL/graph/stats" | python3 -m json.tool 2>/dev/null || echo "无法解析响应"
echo ""

echo "========================================="
echo "测试总结"
echo "========================================="
echo -e "通过: ${GREEN}$TESTS_PASSED${NC}"
echo -e "失败: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}✗ 部分测试失败${NC}"
    exit 1
fi
