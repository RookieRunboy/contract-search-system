#!/bin/bash

# 合同智能检索项目开发调试启动脚本
# 说明：启动后端 API（自动热重载）+ 前端 Vite 开发服务器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOG_DIR="$PROJECT_ROOT/logs"
VENV_DIR="$PROJECT_ROOT/contract_env"

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查命令
check_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        log_error "$1 未安装或不在 PATH 中"
        return 1
    fi
    return 0
}

# 端口占用检查
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# 等待服务可用
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    log_info "等待 $service_name 启动..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            log_success "$service_name 已启动"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    log_warning "$service_name 检测超时，请手动确认"
    return 1
}

create_log_dir() {
    mkdir -p "$LOG_DIR"
}

# 安装依赖
install_dependencies() {
    log_info "检查并安装依赖..."

    # 后端依赖
    if [ -f "$BACKEND_DIR/requirements.txt" ]; then
        log_info "确认后端依赖..."
        if [ -d "$VENV_DIR" ]; then
            source "$VENV_DIR/bin/activate"
            log_info "已激活虚拟环境 contract_env"
        fi
        pip install -r "$BACKEND_DIR/requirements.txt" > "$LOG_DIR/backend-install.log" 2>&1 && \
            log_success "后端依赖已准备就绪" || {
                log_error "安装后端依赖失败，详见 $LOG_DIR/backend-install.log"
                exit 1
            }
    fi

    # 前端依赖
    if [ -f "$FRONTEND_DIR/package.json" ]; then
        log_info "确认前端依赖..."
        cd "$FRONTEND_DIR"
        if [ ! -d "node_modules" ]; then
            if check_command npm; then
                npm install > "$LOG_DIR/frontend-install.log" 2>&1 && \
                    log_success "前端依赖安装完成" || {
                        log_error "安装前端依赖失败，详见 $LOG_DIR/frontend-install.log"
                        exit 1
                    }
            elif check_command yarn; then
                yarn install > "$LOG_DIR/frontend-install.log" 2>&1 && \
                    log_success "前端依赖安装完成" || {
                        log_error "安装前端依赖失败，详见 $LOG_DIR/frontend-install.log"
                        exit 1
                    }
            else
                log_error "请先安装 npm 或 yarn"
                exit 1
            fi
        else
            log_success "前端依赖已安装"
        fi
    fi
}

# 启动 Elasticsearch（与 start.sh 保持一致）
start_elasticsearch() {
    log_info "检查 Elasticsearch 状态..."
    if curl -s -f "http://localhost:9200" >/dev/null 2>&1; then
        log_success "Elasticsearch 已在运行"
        return 0
    fi

    if ! check_command docker; then
        log_error "未检测到 Elasticsearch，也未安装 Docker，无法自动启动"
        exit 1
    fi

    log_info "启动 Elasticsearch Docker 容器..."
    if docker ps -a --format 'table {{.Names}}' | grep -q "^es$"; then
        if docker ps --format 'table {{.Names}}' | grep -q "^es$"; then
            log_success "Elasticsearch 容器已在运行"
        else
            docker start es
        fi
    else
        docker run -d --name es \
            -p 9200:9200 \
            -e discovery.type=single-node \
            -e xpack.security.enabled=false \
            -e ES_JAVA_OPTS="-Xms2g -Xmx2g" \
            docker.elastic.co/elasticsearch/elasticsearch:8.13.4
    fi

    wait_for_service "http://localhost:9200" "Elasticsearch"
}

# 创建索引
create_index() {
    local unified_index="contracts_unified"

    log_info "检查 $unified_index 索引..."
    if curl -s -f "http://localhost:9200/${unified_index}" >/dev/null 2>&1; then
        log_success "索引 ${unified_index} 已存在"
        return 0
    fi

    log_info "创建 Elasticsearch 索引 (${unified_index})..."
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    cd "$BACKEND_DIR"
    python create_unified_index.py > "$LOG_DIR/es-index.log" 2>&1 && \
        log_success "${unified_index} 索引创建完成" || {
            log_error "索引创建失败，详见 $LOG_DIR/es-index.log"
            exit 1
        }
}

# 启动后端（开发模式，热重载）
start_backend_dev() {
    log_info "启动后端 API (reload 模式)..."

    if check_port 8006; then
        log_warning "端口 8006 已被占用，尝试停止现有服务..."
        pkill -f "contractApi.py" || true
        pkill -f "uvicorn" || true
        sleep 2
    fi

    cd "$BACKEND_DIR"
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
    fi

    nohup uvicorn contractApi:app --host 0.0.0.0 --port 8006 --reload > "$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$LOG_DIR/backend.pid"

    wait_for_service "http://localhost:8006/health" "后端服务"
    log_success "后端服务已启动 (PID: $BACKEND_PID)"
}

# 启动前端开发服务器（Vite）
start_frontend_dev() {
    log_info "启动前端开发服务器 (Vite)..."

    if check_port 5173; then
        log_warning "端口 5173 已被占用，尝试停止现有服务..."
        pkill -f "vite" || true
        pkill -f "npm.*dev" || true
        sleep 2
    fi

    cd "$FRONTEND_DIR"
    local run_cmd
    if check_command npm; then
        run_cmd=(npm run dev -- --host 0.0.0.0 --port 5173)
    elif check_command yarn; then
        run_cmd=(yarn dev --host 0.0.0.0 --port 5173)
    else
        log_error "请先安装 npm 或 yarn"
        exit 1
    fi

    nohup "${run_cmd[@]}" > "$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$LOG_DIR/frontend.pid"

    wait_for_service "http://localhost:5173" "前端开发服务器"
    log_success "前端开发服务器已启动 (PID: $FRONTEND_PID)"
}

show_status() {
    echo ""
    log_success "========== 开发模式启动完成 =========="
    echo ""
    echo "📋 服务入口:"
    echo "  • 前端开发界面: http://localhost:5173"
    echo "  • 后端 API: http://localhost:8006"
    echo "  • API 文档: http://localhost:8006/docs"
    echo ""
    echo "📝 日志文件:"
    echo "  • 后端日志: $LOG_DIR/backend.log"
    echo "  • 前端日志: $LOG_DIR/frontend.log"
    echo ""
    echo "🛑 停止服务: ./stop.sh"
    echo ""
}

main() {
    echo ""
    log_info "========== 启动开发调试环境 =========="
    echo ""

    create_log_dir

    if ! check_command python && ! check_command python3; then
        log_error "请先安装 Python"
        exit 1
    fi

    if ! check_command curl; then
        log_error "请先安装 curl"
        exit 1
    fi

    start_elasticsearch
    install_dependencies
    create_index
    start_backend_dev
    start_frontend_dev
    show_status
}

main "$@"
