#!/bin/bash

# 合同智能检索项目配置优化脚本
# 此脚本用于启用高级PDF处理功能（OCR、复杂PDF解析等）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

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

# 检查系统类型
detect_system() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# 安装Tesseract OCR
install_tesseract() {
    local system=$(detect_system)
    
    log_info "安装 Tesseract OCR..."
    
    case $system in
        "macos")
            if command -v brew &> /dev/null; then
                brew install tesseract tesseract-lang
                log_success "Tesseract OCR 安装完成 (macOS)"
            else
                log_error "请先安装 Homebrew: https://brew.sh/"
                return 1
            fi
            ;;
        "linux")
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-chi-tra
                log_success "Tesseract OCR 安装完成 (Ubuntu/Debian)"
            elif command -v yum &> /dev/null; then
                sudo yum install -y epel-release
                sudo yum install -y tesseract tesseract-langpack-chi_sim
                log_success "Tesseract OCR 安装完成 (CentOS/RHEL)"
            else
                log_error "不支持的 Linux 发行版"
                return 1
            fi
            ;;
        *)
            log_error "不支持的操作系统"
            return 1
            ;;
    esac
}

# 安装高级PDF处理依赖
install_advanced_deps() {
    log_info "安装高级PDF处理依赖..."
    
    # 激活虚拟环境
    if [ -d "$PROJECT_ROOT/contract_env" ]; then
        source "$PROJECT_ROOT/contract_env/bin/activate"
        log_info "已激活虚拟环境 contract_env"
    fi
    
    cd "$BACKEND_DIR"
    
    # 创建增强版requirements.txt
    cat > requirements_advanced.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
elasticsearch==8.11.0
sentence-transformers==3.0.1
PyPDF2==3.0.1
python-multipart==0.0.6
requests==2.31.0
pdfplumber==0.10.4
pytesseract==0.3.10
pdf2image==1.17.0
Pillow==10.4.0
PyMuPDF==1.24.14
opencv-python==4.10.0.84
numpy==1.26.4
EOF
    
    pip install -r requirements_advanced.txt
    log_success "高级PDF处理依赖安装完成"
}

# 切换到高级PDF提取器
enable_advanced_extractor() {
    log_info "启用高级PDF提取器..."
    
    cd "$BACKEND_DIR"
    
    # 备份当前的简化版本
    if [ -f "pdfToElasticSearch.py" ]; then
        cp pdfToElasticSearch.py pdfToElasticSearch_simple.py
        log_info "已备份简化版PDF提取器"
    fi
    
    # 修改导入语句，使用增强版提取器
    sed -i.bak 's/from simple_pdf_extractor_backup import SimplePDFExtractor/from enhanced_pdf_extractor import EnhancedPDFExtractor/' pdfToElasticSearch.py
    sed -i.bak 's/self.extractor = SimplePDFExtractor()/self.extractor = EnhancedPDFExtractor()/' pdfToElasticSearch.py
    
    log_success "高级PDF提取器已启用"
}

# 恢复简化版本
disable_advanced_extractor() {
    log_info "恢复简化PDF提取器..."
    
    cd "$BACKEND_DIR"
    
    # 恢复简化版本的导入
    sed -i.bak 's/from enhanced_pdf_extractor import EnhancedPDFExtractor/from simple_pdf_extractor_backup import SimplePDFExtractor/' pdfToElasticSearch.py
    sed -i.bak 's/self.extractor = EnhancedPDFExtractor()/self.extractor = SimplePDFExtractor()/' pdfToElasticSearch.py
    
    log_success "简化PDF提取器已恢复"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  enable    启用高级PDF处理功能（包括OCR）"
    echo "  disable   禁用高级PDF处理功能（使用简化版本）"
    echo "  status    查看当前配置状态"
    echo "  help      显示帮助信息"
    echo ""
    echo "说明:"
    echo "  高级功能包括：OCR识别、复杂PDF解析、表格提取等"
    echo "  简化功能仅包括：基础PDF文本提取"
    echo ""
    echo "示例:"
    echo "  $0 enable     # 启用高级功能"
    echo "  $0 disable    # 切换到简化模式"
    echo "  $0 status     # 查看当前状态"
}

# 检查当前状态
check_status() {
    log_info "检查当前PDF处理器配置..."
    
    cd "$BACKEND_DIR"
    
    if grep -q "SimplePDFExtractor" pdfToElasticSearch.py; then
        echo "当前模式: 简化版PDF处理器"
        echo "功能: 基础PDF文本提取（PyPDF2）"
    elif grep -q "EnhancedPDFExtractor" pdfToElasticSearch.py; then
        echo "当前模式: 高级PDF处理器"
        echo "功能: OCR识别、复杂PDF解析、表格提取"
    else
        echo "当前模式: 未知"
    fi
    
    # 检查依赖
    echo ""
    echo "依赖检查:"
    
    if command -v tesseract &> /dev/null; then
        echo "✅ Tesseract OCR: 已安装"
    else
        echo "❌ Tesseract OCR: 未安装"
    fi
    
    # 激活虚拟环境进行Python包检查
    if [ -d "$PROJECT_ROOT/contract_env" ]; then
        source "$PROJECT_ROOT/contract_env/bin/activate"
        
        python -c "import pytesseract; print('✅ pytesseract: 已安装')" 2>/dev/null || echo "❌ pytesseract: 未安装"
        python -c "import pdf2image; print('✅ pdf2image: 已安装')" 2>/dev/null || echo "❌ pdf2image: 未安装"
        python -c "import pdfplumber; print('✅ pdfplumber: 已安装')" 2>/dev/null || echo "❌ pdfplumber: 未安装"
    fi
}

# 主函数
main() {
    case "${1:-help}" in
        "enable")
            echo ""
            log_info "========== 启用高级PDF处理功能 =========="
            echo ""
            install_tesseract
            install_advanced_deps
            enable_advanced_extractor
            echo ""
            log_success "高级PDF处理功能已启用！"
            log_info "请重新启动项目以应用更改: ./stop.sh && ./start.sh"
            ;;
        "disable")
            echo ""
            log_info "========== 禁用高级PDF处理功能 =========="
            echo ""
            disable_advanced_extractor
            echo ""
            log_success "已切换到简化PDF处理模式！"
            log_info "请重新启动项目以应用更改: ./stop.sh && ./start.sh"
            ;;
        "status")
            echo ""
            log_info "========== PDF处理器状态 =========="
            echo ""
            check_status
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"