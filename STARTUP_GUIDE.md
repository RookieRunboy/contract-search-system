# 合同智能检索项目一键启动说明

本项目现已支持一键启动！通过提供的脚本可以自动启动所有必要服务。

## 🚀 快速开始

### 1. 给脚本添加执行权限
```bash
chmod +x start.sh stop.sh
```

### 2. 一键启动项目
```bash
./start.sh
```

### 3. 停止项目
```bash
./stop.sh
```

### 4. 访问应用
- **前端应用**: http://localhost:5173
- **后端API**: http://localhost:8006
- **API文档**: http://localhost:8006/docs
- **Elasticsearch**: http://localhost:9200

## ✅ 启动成功标志

当看到以下输出时，表示启动成功：
```
[SUCCESS] ========== 服务启动完成 ==========

📋 服务状态:
  • Elasticsearch: http://localhost:9200
  • 后端 API: http://localhost:8006
  • 前端应用: http://localhost:5173
  • API 文档: http://localhost:8006/docs
```

## 📋 详细说明

### 启动脚本 (start.sh)

#### 功能概述
- ✅ 自动检查并启动 Elasticsearch (Docker)
- ✅ 自动安装Python和Node.js依赖
- ✅ 自动创建Elasticsearch索引
- ✅ 启动后端FastAPI服务 (端口: 8006)
- ✅ 启动前端React应用 (端口: 5173)
- ✅ 实时服务健康检查
- ✅ 自动错误处理和重试机制

#### 启动顺序
1. **Elasticsearch**: 使用Docker启动，如果容器已存在则重用
2. **安装依赖**: 自动安装backend/requirements.txt和frontend/package.json中的依赖
3. **创建索引**: 运行elasticSearchSettingVector.py创建contracts_vector索引
4. **后端服务**: 启动FastAPI服务在8006端口
5. **前端服务**: 启动Vite开发服务器在5173端口

#### 智能特性
- 🔄 **依赖版本管理**: 自动解决sentence-transformers版本兼容问题
- 🔧 **虚拟环境支持**: 自动检测并使用contract_env虚拟环境
- 📊 **服务监控**: 实时检查服务状态，确保成功启动
- ⚡ **快速恢复**: 如果容器已存在，直接重用而不重新创建

## ⚙️ PDF处理器配置

项目支持两种PDF处理模式：

### 📝 简化模式（默认）
- **功能**: 基础PDF文本提取（PyPDF2）
- **优点**: 启动快速、依赖简单、稳定性高
- **适用**: 文字类合同、基础测试

### 🔍 高级模式（可选）
- **功能**: OCR识别、复杂PDF解析、表格提取
- **优点**: 支持图片文字、扫描件、复杂格式
- **适用**: 全功能生产环境

### 切换命令
```bash
# 查看当前状态
./configure.sh status

# 启用高级功能
./configure.sh enable

# 切换到简化模式
./configure.sh disable
```

#### 基本用法
```bash
./stop.sh                # 停止前后端服务，保留Elasticsearch
./stop.sh --with-es      # 停止所有服务包括Elasticsearch
./stop.sh --clean-logs   # 停止服务并清理日志文件
./stop.sh --help         # 显示帮助信息
```

#### 功能
- 安全停止所有服务进程
- 可选择性停止Elasticsearch
- 清理PID文件和日志文件
- 多重保险机制确保进程正确停止

## 前置要求

### 必需软件
- **Docker**: 用于运行Elasticsearch
- **Python 3.10+**: 后端服务
- **Node.js**: 前端开发
- **npm 或 yarn**: 前端包管理器

### 可选配置
- **虚拟环境**: 脚本会自动检测并使用 `contract_env` 虚拟环境
- **Conda环境**: 可使用 `合同检索技术说明/environment.yml` 创建环境

## 日志和监控

### 日志文件位置
- 后端日志: `logs/backend.log`
- 前端日志: `logs/frontend.log`
- PID文件: `logs/backend.pid`, `logs/frontend.pid`

### 实时查看日志
```bash
# 查看后端日志
tail -f logs/backend.log

# 查看前端日志
tail -f logs/frontend.log

# 查看所有日志
tail -f logs/*.log
```

## 故障排除

### 常见问题

1. **端口被占用**
   - 脚本会自动检测并尝试停止占用端口的进程
   - 手动停止: `lsof -ti:8006 | xargs kill`

2. **Docker未启动**
   - 确保Docker Desktop正在运行
   - 检查: `docker ps`

3. **依赖安装失败**
   - 检查网络连接
   - 清理缓存: `pip cache purge`, `npm cache clean --force`

4. **虚拟环境问题**
   - 重新创建虚拟环境: `python -m venv contract_env`
   - 或使用conda: `conda env create -f 合同检索技术说明/environment.yml`

### 手动启动步骤（备用方案）

如果自动脚本出现问题，可以手动按以下步骤启动：

1. **启动Elasticsearch**
   ```bash
   docker run -d --name es -p 9200:9200 -e discovery.type=single-node -e xpack.security.enabled=false docker.elastic.co/elasticsearch/elasticsearch:8.13.4
   ```

2. **创建索引**
   ```bash
   cd backend && python elasticSearchSettingVector.py
   ```

3. **启动后端**
   ```bash
   cd backend && python contractApi.py
   ```

4. **启动前端**
   ```bash
   cd frontend && npm run dev
   ```

## 开发建议

### 开发模式
- 前端支持热重载，修改代码会自动刷新
- 后端修改需要重启服务
- 可以单独启动前端或后端进行开发

### API测试
- 使用提供的 `test_api_local.py` 进行API测试
- 访问 http://localhost:8006/docs 查看API文档
- 使用 `apiTest.py` 进行功能测试

### 数据管理
- 上传的PDF文件处理后存储在Elasticsearch中
- 使用 `/documents` 接口查看已上传文档
- 使用 `/clear-index` 接口清空所有数据

---

现在您可以通过 `./start.sh` 一键启动整个项目！