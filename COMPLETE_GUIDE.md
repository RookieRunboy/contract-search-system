# 🔥 合同智能检索项目 - 完整使用指南

## 🎯 项目概述

本项目是一个基于 **向量检索 + 关键词检索** 的混合合同智能检索系统，具备以下核心功能：

- 📄 **PDF上传与解析**：支持页级拆分与向量化
- 🔍 **混合检索**：向量召回 + 关键词匹配
- 🗑️ **文档管理**：按文件名或页码删除
- 📊 **系统监控**：Elasticsearch 状态自检
- 🚀 **一键部署**：本地与服务器部署支持

---

## ⚡ 一键启动（推荐）

### 快速开始
```bash
# 1. 给脚本执行权限
chmod +x start.sh stop.sh configure.sh

# 2. 启动项目
./start.sh

# 3. 访问应用
# 前端: http://localhost:5173
# API:  http://localhost:8006/docs
```

### 服务状态检查
```bash
# 检查所有服务
curl http://localhost:8006/health

# 检查前端
curl http://localhost:5173

# 检查Elasticsearch
curl http://localhost:9200
```

---

## 🛠️ 技术架构

| 组件 | 技术栈 | 端口 | 说明 |
|------|--------|------|------|
| **前端** | React + TypeScript + Vite + Antd | 5173 | 用户界面 |
| **后端** | FastAPI + Python | 8006 | API服务 |
| **搜索引擎** | Elasticsearch | 9200 | 数据存储与检索 |
| **向量模型** | sentence-transformers | - | 文本向量化 |
| **PDF处理** | PyPDF2/Enhanced | - | 文档解析 |

---

## 📋 功能详解

### 1. 文档上传 📤
```bash
# API上传
curl -X POST "http://localhost:8006/document/add" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@合同.pdf"
```

### 2. 智能搜索 🔍
```bash
# 混合检索
curl -G "http://localhost:8006/document/search" \
  --data-urlencode "query=银华基金" \
  --data-urlencode "top_k=3"
```

### 3. 文档管理 📂
```bash
# 查看文档列表
curl http://localhost:8006/documents

# 删除文档
curl -X DELETE "http://localhost:8006/document/delete?filename=合同名称"

# 清空索引
curl -X DELETE "http://localhost:8006/clear-index"
```

---

## ⚙️ 高级配置

### PDF处理器配置
```bash
# 查看当前配置
./configure.sh status

# 启用高级功能（OCR + 复杂PDF）
./configure.sh enable

# 切换到简化模式（仅基础提取）
./configure.sh disable
```

### 环境变量配置
```bash
# 模型下载加速（可选）
export HF_ENDPOINT=https://hf-mirror.com

# Elasticsearch配置
export ES_HOST=http://localhost:9200
export ES_INDEX=contracts_vector
```

---

## 🐳 Docker 部署（生产环境）

### 1. 创建 docker-compose.yml
```yaml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.13.4
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  backend:
    build: ./backend
    ports:
      - "8006:8006"
    depends_on:
      - elasticsearch
    environment:
      - ES_HOST=http://elasticsearch:9200

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend

volumes:
  es_data:
```

### 2. 启动服务
```bash
docker-compose up -d
```

---

## 🔧 故障排除

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 🔴 **端口被占用** | `lsof -ti:8006 \| xargs kill` |
| 🔴 **Docker未启动** | 启动 Docker Desktop |
| 🔴 **依赖安装失败** | `pip cache purge && ./start.sh` |
| 🔴 **模型下载慢** | 设置 `HF_ENDPOINT` 环境变量 |
| 🔴 **虚拟环境问题** | `python -m venv contract_env` |

### 日志查看
```bash
# 实时查看后端日志
tail -f logs/backend.log

# 实时查看前端日志  
tail -f logs/frontend.log

# 查看所有日志
tail -f logs/*.log
```

### 重置项目
```bash
# 完全重置（包括停止Elasticsearch）
./stop.sh --with-es --clean-logs

# 清理并重新开始
rm -rf logs/ contract_env/ node_modules/
./start.sh
```

---

## 📊 性能优化

### 1. Elasticsearch 优化
```bash
# 调整JVM内存（根据系统内存）
export ES_JAVA_OPTS="-Xms4g -Xmx4g"

# 索引设置优化
curl -X PUT "localhost:9200/contracts_vector/_settings" \
  -H 'Content-Type: application/json' \
  -d '{"refresh_interval": "5s"}'
```

### 2. 向量模型优化
```python
# 使用更小的模型（推理更快）
model_name = "BAAI/bge-small-zh"

# 使用GPU加速（如果可用）
model = SentenceTransformer(model_name, device='cuda')
```

---

## 🚀 生产部署建议

### 1. 安全配置
- ✅ 启用 Elasticsearch 安全认证
- ✅ 使用 HTTPS（Nginx + SSL）
- ✅ 配置防火墙规则
- ✅ 定期备份数据

### 2. 监控告警
- ✅ 配置服务监控（Prometheus + Grafana）
- ✅ 设置日志聚合（ELK Stack）
- ✅ 健康检查接口：`/health`

### 3. 扩展性
- ✅ Elasticsearch 集群部署
- ✅ 负载均衡（Nginx）
- ✅ 容器编排（Kubernetes）

---

## 🤝 API 快速参考

| 接口 | 方法 | 说明 | 示例 |
|------|------|------|------|
| `/` | GET | 系统信息 | `curl localhost:8006/` |
| `/health` | GET | 健康检查 | `curl localhost:8006/health` |
| `/document/add` | POST | 上传文档 | 见上文示例 |
| `/document/search` | GET | 搜索文档 | 见上文示例 |
| `/documents` | GET | 文档列表 | `curl localhost:8006/documents` |
| `/document/delete` | DELETE | 删除文档 | 见上文示例 |
| `/docs` | GET | API文档 | http://localhost:8006/docs |

---

## 📚 开发指南

### 本地开发
```bash
# 仅启动后端（用于API开发）
cd backend && python contractApi.py

# 仅启动前端（用于UI开发）  
cd frontend && npm run dev

# 开发模式特性
# - 热重载：前端代码自动刷新
# - API调试：访问 /docs 查看接口文档
# - 日志监控：实时查看 logs/ 目录
```

### 测试
```bash
# API功能测试
python backend/test_api_local.py --check

# 上传测试
python backend/test_api_local.py -U "./test.pdf"

# 搜索测试  
python backend/test_api_local.py -q "关键词" --top-k 5
```

---

## 🎉 总结

恭喜！您已经成功部署了合同智能检索系统。现在您可以：

1. ✅ **上传合同文档** - 支持PDF格式，自动解析和向量化
2. ✅ **智能搜索** - 混合检索技术，高精度匹配
3. ✅ **文档管理** - 完整的CRUD操作
4. ✅ **系统监控** - 实时健康状态检查
5. ✅ **扩展配置** - 灵活的PDF处理器切换

### 下一步建议：
- 🔄 尝试上传一些测试合同文档
- 🔍 测试不同的搜索关键词
- ⚙️ 根据需要切换PDF处理模式
- 📊 监控系统性能和日志

### 技术支持：
- 📖 详细文档：查看项目根目录的各个 `.md` 文件
- 🔧 配置工具：`./configure.sh help`
- 🔍 API文档：http://localhost:8006/docs
- 📋 系统状态：`./configure.sh status`

**项目已就绪，开始您的智能检索之旅吧！** 🚀