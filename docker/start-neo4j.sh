#!/bin/bash
# Neo4j 启动辅助脚本

echo "检查Neo4j容器状态..."

# 检查是否有Neo4j容器在运行
RUNNING_NEO4J=$(docker ps --filter "ancestor=neo4j" --format "{{.Names}}" | head -1)

if [ -n "$RUNNING_NEO4J" ]; then
    echo "发现运行中的Neo4j容器: $RUNNING_NEO4J"
    echo ""
    echo "选项:"
    echo "1. 使用现有容器 $RUNNING_NEO4J (推荐)"
    echo "2. 停止现有容器并启动新的 medkg-neo4j"
    echo ""
    read -p "请选择 (1/2): " choice
    
    if [ "$choice" = "1" ]; then
        echo "使用现有容器: $RUNNING_NEO4J"
        echo ""
        echo "请在 backend/.env 中配置:"
        echo "NEO4J_URI=bolt://localhost:7687"
        echo "NEO4J_USER=neo4j"
        echo "NEO4J_PASSWORD=<您的密码>"
        echo ""
        echo "常见密码: neo4j, password, medkg2024"
        
    elif [ "$choice" = "2" ]; then
        echo "停止现有容器..."
        docker stop $RUNNING_NEO4J
        
        echo "启动新容器..."
        docker-compose -f docker-compose-neo4j.yml up -d
        
        echo ""
        echo "新容器已启动！"
        echo "认证信息:"
        echo "  用户名: neo4j"
        echo "  密码: medkg2024"
        echo "  访问: http://localhost:7474"
    else
        echo "无效选择"
        exit 1
    fi
else
    echo "没有运行中的Neo4j容器，启动新容器..."
    docker-compose -f docker-compose-neo4j.yml up -d
    
    echo ""
    echo "容器已启动！"
    echo "认证信息:"
    echo "  用户名: neo4j"
    echo "  密码: medkg2024"
    echo "  访问: http://localhost:7474"
fi

echo ""
echo "等待Neo4j启动完成（约30秒）..."
sleep 5

echo "检查容器状态..."
docker ps | grep neo4j
