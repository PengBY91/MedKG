#!/bin/bash

# MedKG 服务管理脚本
# 支持启动、停止、重启前后端服务

# 配置
BACKEND_DIR="/Users/steve/work/智能体平台/MedKG/backend"
FRONTEND_DIR="/Users/steve/work/智能体平台/MedKG/frontend"
CONDA_ENV="medical"
BACKEND_PORT=8001
FRONTEND_PORT=3000

# PID文件
BACKEND_PID_FILE="/tmp/medkg_backend.pid"
FRONTEND_PID_FILE="/tmp/medkg_frontend.pid"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的
消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查进程是否运行
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# 通过端口查找并杀死进程（排除Docker容器）
kill_by_port() {
    local port=$1
    # 获取端口上的所有进程
    local pids=$(lsof -ti :$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        # 过滤出Python和Node进程，排除Docker相关进程
        local filtered_pids=""
        for pid in $pids; do
            local cmd=$(ps -p $pid -o comm= 2>/dev/null)
            # 只杀死python和node进程
            if [[ "$cmd" == *"python"* ]] || [[ "$cmd" == *"node"* ]] || [[ "$cmd" == *"uvicorn"* ]]; then
                filtered_pids="$filtered_pids $pid"
            fi
        done
        
        if [ -n "$filtered_pids" ]; then
            print_info "发现端口 $port 被占用，正在停止MedKG进程..."
            echo "$filtered_pids" | xargs kill -9 2>/dev/null
            sleep 1
        fi
    fi
}

# 启动后端
start_backend() {
    if is_running "$BACKEND_PID_FILE"; then
        print_warn "后端服务已在运行中"
        return 0
    fi
    
    # 检查端口占用
    kill_by_port $BACKEND_PORT
    
    print_info "启动后端服务..."
    
    # 激活conda环境并启动
    cd "$BACKEND_DIR"
    source ~/miniforge3/etc/profile.d/conda.sh
    conda activate $CONDA_ENV
    
    nohup uvicorn app.main:app --reload --host 127.0.0.1 --port $BACKEND_PORT > /tmp/medkg_backend.log 2>&1 &
    echo $! > "$BACKEND_PID_FILE"
    
    sleep 2
    
    if is_running "$BACKEND_PID_FILE"; then
        print_info "后端服务启动成功 (PID: $(cat $BACKEND_PID_FILE))"
        print_info "访问地址: http://127.0.0.1:$BACKEND_PORT"
        print_info "日志文件: /tmp/medkg_backend.log"
        return 0
    else
        print_error "后端服务启动失败，请查看日志: /tmp/medkg_backend.log"
        return 1
    fi
}

# 启动前端
start_frontend() {
    if is_running "$FRONTEND_PID_FILE"; then
        print_warn "前端服务已在运行中"
        return 0
    fi
    
    # 检查端口占用
    kill_by_port $FRONTEND_PORT
    
    print_info "启动前端服务..."
    
    cd "$FRONTEND_DIR"
    nohup npm run dev > /tmp/medkg_frontend.log 2>&1 &
    echo $! > "$FRONTEND_PID_FILE"
    
    sleep 3
    
    if is_running "$FRONTEND_PID_FILE"; then
        print_info "前端服务启动成功 (PID: $(cat $FRONTEND_PID_FILE))"
        print_info "访问地址: http://localhost:$FRONTEND_PORT"
        print_info "日志文件: /tmp/medkg_frontend.log"
        return 0
    else
        print_error "前端服务启动失败，请查看日志: /tmp/medkg_frontend.log"
        return 1
    fi
}

# 停止后端
stop_backend() {
    if is_running "$BACKEND_PID_FILE"; then
        local pid=$(cat "$BACKEND_PID_FILE")
        print_info "停止后端服务 (PID: $pid)..."
        kill "$pid" 2>/dev/null
        sleep 1
        
        # 如果还在运行，强制杀死
        if ps -p "$pid" > /dev/null 2>&1; then
            kill -9 "$pid" 2>/dev/null
        fi
        
        rm -f "$BACKEND_PID_FILE"
        print_info "后端服务已停止"
    else
        print_warn "后端服务未运行"
    fi
    
    # 清理端口
    kill_by_port $BACKEND_PORT
}

# 停止前端
stop_frontend() {
    if is_running "$FRONTEND_PID_FILE"; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        print_info "停止前端服务 (PID: $pid)..."
        kill "$pid" 2>/dev/null
        sleep 1
        
        # 如果还在运行，强制杀死
        if ps -p "$pid" > /dev/null 2>&1; then
            kill -9 "$pid" 2>/dev/null
        fi
        
        rm -f "$FRONTEND_PID_FILE"
        print_info "前端服务已停止"
    else
        print_warn "前端服务未运行"
    fi
    
    # 清理端口
    kill_by_port $FRONTEND_PORT
}

# 查看状态
status() {
    echo "========================================="
    echo "MedKG 服务状态"
    echo "========================================="
    
    # 后端状态
    if is_running "$BACKEND_PID_FILE"; then
        local pid=$(cat "$BACKEND_PID_FILE")
        print_info "后端服务: ${GREEN}运行中${NC} (PID: $pid)"
        echo "  地址: http://127.0.0.1:$BACKEND_PORT"
        echo "  日志: /tmp/medkg_backend.log"
    else
        print_warn "后端服务: ${RED}未运行${NC}"
    fi
    
    echo ""
    
    # 前端状态
    if is_running "$FRONTEND_PID_FILE"; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        print_info "前端服务: ${GREEN}运行中${NC} (PID: $pid)"
        echo "  地址: http://localhost:$FRONTEND_PORT"
        echo "  日志: /tmp/medkg_frontend.log"
    else
        print_warn "前端服务: ${RED}未运行${NC}"
    fi
    
    echo "========================================="
}

# 查看日志
logs() {
    local service=$1
    
    case $service in
        backend)
            if [ -f /tmp/medkg_backend.log ]; then
                tail -f /tmp/medkg_backend.log
            else
                print_error "后端日志文件不存在"
            fi
            ;;
        frontend)
            if [ -f /tmp/medkg_frontend.log ]; then
                tail -f /tmp/medkg_frontend.log
            else
                print_error "前端日志文件不存在"
            fi
            ;;
        *)
            print_error "请指定服务: backend 或 frontend"
            echo "用法: $0 logs [backend|frontend]"
            ;;
    esac
}

# 显示帮助
show_help() {
    cat << EOF
MedKG 服务管理脚本

用法: $0 [命令] [选项]

命令:
  start           启动所有服务（前端+后端）
  stop            停止所有服务
  restart         重启所有服务
  reload          重新加载所有服务（同restart）
  status          查看服务状态
  logs [service]  查看日志（backend/frontend）
  
  start-backend   仅启动后端
  stop-backend    仅停止后端
  start-frontend  仅启动前端
  stop-frontend   仅停止前端

示例:
  $0 start              # 启动所有服务
  $0 stop               # 停止所有服务
  $0 restart            # 重启所有服务
  $0 status             # 查看状态
  $0 logs backend       # 查看后端日志
  $0 start-backend      # 仅启动后端

配置:
  后端端口: $BACKEND_PORT
  前端端口: $FRONTEND_PORT
  Conda环境: $CONDA_ENV

EOF
}

# 主命令处理
case "$1" in
    start)
        print_info "启动 MedKG 服务..."
        start_backend
        start_frontend
        echo ""
        status
        ;;
    stop)
        print_info "停止 MedKG 服务..."
        stop_backend
        stop_frontend
        ;;
    restart|reload)
        print_info "重启 MedKG 服务..."
        stop_backend
        stop_frontend
        sleep 2
        start_backend
        start_frontend
        echo ""
        status
        ;;
    start-backend)
        start_backend
        ;;
    stop-backend)
        stop_backend
        ;;
    start-frontend)
        start_frontend
        ;;
    stop-frontend)
        stop_frontend
        ;;
    status)
        status
        ;;
    logs)
        logs "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "未知命令: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
