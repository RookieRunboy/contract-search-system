#!/bin/bash

# 合同智能检索项目停止脚本
# 作者: AI Assistant
# 日期: $(date +%Y-%m-%d)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 停止进程
stop_process() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            log_info "停止 $service_name (PID: $pid)..."
            kill $pid
            sleep 2
            
            # 如果进程仍在运行，强制停止
            if ps -p $pid > /dev/null 2>&1; then
                log_warning "强制停止 $service_name..."
                kill -9 $pid
            fi
            
            log_success "$service_name 已停止"
        else
            log_warning "$service_name 进程不存在 (PID: $pid)"
        fi
        rm -f "$pid_file"
    else
        log_warning "$service_name PID 文件不存在"
    fi
}

# 停止后端服务
stop_backend() {
    log_info "停止后端服务..."
    
    # 通过PID文件停止
    stop_process "$PROJECT_ROOT/logs/backend.pid" "后端服务"
    
    # 通过进程名停止（备用方案）
    pkill -f "contractApi.py" || true
    
    # 通过端口停止（备用方案）
    local pid=$(lsof -ti:8006)
    if [ ! -z "$pid" ]; then
        log_info "通过端口停止后端服务..."
        kill $pid || true
    fi
}

# 停止前端服务
stop_frontend() {
    log_info "停止前端服务..."
    
    # 通过PID文件停止
    stop_process "$PROJECT_ROOT/logs/frontend.pid" "前端服务"
    
    # 通过进程名停止（备用方案）
    pkill -f "vite" || true
    pkill -f "npm.*dev" || true
    pkill -f "yarn.*dev" || true
    
    # 通过端口停止（备用方案）
    local pid=$(lsof -ti:5173)
    if [ ! -z "$pid" ]; then
        log_info "通过端口停止前端服务..."
        kill $pid || true
    fi
}

# 停止Elasticsearch (可选)
stop_elasticsearch() {
    if [ "$1" = "--with-es" ] || [ "$1" = "-e" ]; then
        log_info "停止 Elasticsearch..."
        
        if command -v docker &> /dev/null; then
            if docker ps --format 'table {{.Names}}' | grep -q "^es$"; then
                docker stop es
                log_success "Elasticsearch 已停止"
            else
                log_warning "Elasticsearch 容器未运行"
            fi
        else
            log_warning "Docker 未安装，无法停止 Elasticsearch"
        fi
    else
        log_info "保持 Elasticsearch 运行 (使用 --with-es 参数可同时停止)"
    fi
}

# 清理日志文件
clean_logs() {
    if [ "$1" = "--clean-logs" ] || [ "$1" = "-c" ]; then
        log_info "清理日志文件..."
        rm -f "$PROJECT_ROOT/logs/backend.log"
        rm -f "$PROJECT_ROOT/logs/frontend.log"
        log_success "日志文件已清理"
    fi
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -e, --with-es     同时停止 Elasticsearch"
    echo "  -c, --clean-logs  清理日志文件"
    echo "  -h, --help        显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                # 停止前后端服务"
    echo "  $0 --with-es      # 停止所有服务包括 Elasticsearch"
    echo "  $0 --clean-logs   # 停止服务并清理日志"
}

# 主函数
main() {
    # 检查帮助参数
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_help
        exit 0
    fi
    
    echo ""
    log_info "========== 停止合同智能检索项目 =========="
    echo ""
    
    stop_backend
    stop_frontend
    stop_elasticsearch "$@"
    clean_logs "$@"
    
    echo ""
    log_success "========== 项目已停止 =========="
    echo ""
}

# 执行主函数
main "$@"