#!/bin/bash
# 服务器部署启动脚本：设置服务器可访问的模型接口地址后调用通用 start.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export QWEN_API_BASE="${QWEN_API_BASE:-http://qwen3-vl.sdflakjfajdhfaks.com:8000/v1}"

exec "$SCRIPT_DIR/start.sh" "$@"
