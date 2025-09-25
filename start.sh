#!/bin/bash

# 合同智能检索项目一键启动脚本
# 作者: AI Assistant
# 日期: $(date +%Y-%m-%d)

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

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

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装或不在PATH中"
        return 1
    fi
    return 0
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0  # 端口被占用
    else
        return 1  # 端口未被占用
    fi
}

# 等待服务启动
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
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "$service_name 启动超时"
    return 1
}

# 启动 Elasticsearch
start_elasticsearch() {
    log_info "检查 Elasticsearch 状态..."
    
    if curl -s -f "http://localhost:9200" > /dev/null 2>&1; then
        log_success "Elasticsearch 已在运行"
        return 0
    fi
    
    if ! check_command docker; then
        log_error "请先安装 Docker"
        exit 1
    fi
    
    log_info "启动 Elasticsearch Docker 容器..."
    
    # 检查容器是否已存在
    if docker ps -a --format 'table {{.Names}}' | grep -q "^es$"; then
        if docker ps --format 'table {{.Names}}' | grep -q "^es$"; then
            log_success "Elasticsearch 容器已在运行"
        else
            log_info "启动现有的 Elasticsearch 容器..."
            docker start es
        fi
    else
        log_info "创建并启动新的 Elasticsearch 容器..."
        docker run -d --name es \
            -p 9200:9200 \
            -e discovery.type=single-node \
            -e xpack.security.enabled=false \
            -e ES_JAVA_OPTS="-Xms2g -Xmx2g" \
            docker.elastic.co/elasticsearch/elasticsearch:8.13.4
    fi
    
    # 等待 Elasticsearch 启动
    wait_for_service "http://localhost:9200" "Elasticsearch"
}

# 创建索引
create_index() {
    log_info "检查索引状态..."
    
    # 检查索引是否已存在
    if curl -s -f "http://localhost:9200/contracts_vector" > /dev/null 2>&1; then
        log_success "索引 contracts_vector 已存在"
        return 0
    fi
    
    log_info "创建 Elasticsearch 索引..."
    cd "$BACKEND_DIR"
    
    # 激活虚拟环境（如果存在）
    if [ -d "../contract_env" ]; then
        source ../contract_env/bin/activate
        log_info "已激活虚拟环境 contract_env"
    fi
    
    python elasticSearchSettingVector.py
    log_success "索引创建完成"
}

# 安装依赖
install_dependencies() {
    log_info "检查并安装依赖..."
    
    # 检查后端依赖
    cd "$BACKEND_DIR"
    if [ -f "requirements.txt" ]; then
        log_info "安装后端依赖..."
        
        # 激活虚拟环境（如果存在）
        if [ -d "../contract_env" ]; then
            source ../contract_env/bin/activate
            log_info "已激活虚拟环境 contract_env"
        fi
        
        pip install -r requirements.txt
        log_success "后端依赖安装完成"
    fi
    
    # 检查前端依赖
    cd "$FRONTEND_DIR"
    if [ -f "package.json" ]; then
        if [ ! -d "node_modules" ]; then
            log_info "安装前端依赖..."
            if check_command npm; then
                npm install
            elif check_command yarn; then
                yarn install
            else
                log_error "请先安装 npm 或 yarn"
                exit 1
            fi
            log_success "前端依赖安装完成"
        else
            log_success "前端依赖已安装"
        fi
    fi
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    
    if check_port 8006; then
        log_warning "端口 8006 已被占用，尝试停止现有服务..."
        pkill -f "contractApi.py" || true
        sleep 2
    fi
    
    cd "$BACKEND_DIR"
    
    # 激活虚拟环境（如果存在）
    if [ -d "../contract_env" ]; then
        source ../contract_env/bin/activate
        log_info "已激活虚拟环境 contract_env"
    fi
    
    # 确保日志目录存在
    mkdir -p "$PROJECT_ROOT/logs"
    
    # 后台启动后端服务
    nohup python contractApi.py > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PROJECT_ROOT/logs/backend.pid"
    
    # 等待后端启动
    wait_for_service "http://localhost:8006/health" "后端服务"
    log_success "后端服务已启动 (PID: $BACKEND_PID)"
}

# 启动前端服务
build_frontend() {
    log_info "构建前端静态资源..."

    cd "$FRONTEND_DIR"

    # 确保日志目录存在
    mkdir -p "$PROJECT_ROOT/logs"

    if check_command npm; then
        npm run build > "$PROJECT_ROOT/logs/frontend.log" 2>&1
    elif check_command yarn; then
        yarn build > "$PROJECT_ROOT/logs/frontend.log" 2>&1
    else
        log_error "请先安装 npm 或 yarn"
        exit 1
    fi

    if [ $? -eq 0 ]; then
        log_success "前端静态资源构建完成 (访问地址: http://localhost:8006)"
    else
        log_error "前端构建失败，请查看 $PROJECT_ROOT/logs/frontend.log"
        exit 1
    fi
}

# 显示服务状态
show_status() {
    echo ""
    log_success "========== 服务启动完成 =========="
    echo ""
    echo "📋 服务状态:"
    echo "  • Elasticsearch: http://localhost:9200"
    echo "  • 后端 API: http://localhost:8006"
    echo "  • 前端应用: http://localhost:8006"
    echo "  • API 文档: http://localhost:8006/docs"
    echo ""
    echo "📝 日志文件:"
    echo "  • 后端日志: $PROJECT_ROOT/logs/backend.log"
    echo "  • 前端日志: $PROJECT_ROOT/logs/frontend.log"
    echo ""
    echo "🛑 停止服务: ./stop.sh"
    echo ""
}

# 创建日志目录
create_log_dir() {
    mkdir -p "$PROJECT_ROOT/logs"
}

# 主函数
main() {
    echo ""
    log_info "========== 合同智能检索项目启动 =========="
    echo ""
    
    create_log_dir
    
    # 检查基础命令
    if ! check_command python && ! check_command python3; then
        log_error "请先安装 Python"
        exit 1
    fi
    
    if ! check_command curl; then
        log_error "请先安装 curl"
        exit 1
    fi
    
    # 按顺序启动服务
    start_elasticsearch
    install_dependencies
    create_index
    build_frontend
    start_backend
    
    show_status
}

# 执行主函数
main "$@"
