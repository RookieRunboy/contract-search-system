# 合同智能检索系统

一个基于 Elasticsearch 和 AI 向量搜索的智能合同检索系统，支持 PDF 文档上传、文本提取、向量化存储和智能搜索。

## 🚀 功能特性

- **智能文档上传**: 支持 PDF 格式合同文档上传
- **文本提取**: 自动提取 PDF 文档中的文本内容
- **向量化存储**: 使用 sentence-transformers 生成文本向量并存储到 Elasticsearch
- **混合搜索**: 结合传统文本搜索和向量相似度搜索
- **现代化界面**: 基于 Vue 3 + TypeScript 的响应式前端界面
- **RESTful API**: 完整的后端 API 接口
- **一键部署**: 提供自动化启动和停止脚本

## 🏗️ 技术架构

### 后端技术栈
- **FastAPI**: 高性能 Python Web 框架
- **Elasticsearch**: 分布式搜索引擎
- **sentence-transformers**: 文本向量化模型
- **PyPDF2**: PDF 文档处理
- **uvicorn**: ASGI 服务器

### 前端技术栈
- **Vue 3**: 渐进式 JavaScript 框架
- **TypeScript**: 类型安全的 JavaScript
- **Vite**: 现代化构建工具
- **Element Plus**: Vue 3 组件库

### 基础设施
- **Docker**: Elasticsearch 容器化部署
- **Nginx**: 静态文件服务（可选）

## 📦 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- Docker
- Git

### 1. 克隆项目

```bash
git clone https://github.com/RookieRunboy/contract-search-system.git
cd contract-search-system
```

### 2. 一键启动

```bash
# 给脚本执行权限
chmod +x start.sh stop.sh

# 启动所有服务
./start.sh
```

启动脚本会自动完成以下操作：
1. 启动 Elasticsearch Docker 容器
2. 安装 Python 和 Node.js 依赖
3. 创建 Elasticsearch 索引
4. 启动后端 API 服务
5. 构建并部署前端应用

### 3. 访问应用

启动完成后，可以通过以下地址访问：

- **前端应用**: http://localhost:8006
- **后端 API**: http://localhost:8006/docs
- **Elasticsearch**: http://localhost:9200

### 4. 停止服务

```bash
# 停止前后端服务
./stop.sh

# 停止所有服务（包括 Elasticsearch）
./stop.sh --with-es

# 停止服务并清理日志
./stop.sh --clean-logs
```

## 🔧 手动安装

如果需要手动安装和配置，请按照以下步骤：

### 后端安装

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv contract_env
source contract_env/bin/activate  # Linux/Mac
# contract_env\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动 Elasticsearch
docker run -d --name es \
  -p 9200:9200 \
  -e discovery.type=single-node \
  -e xpack.security.enabled=false \
  docker.elastic.co/elasticsearch/elasticsearch:8.13.4

# 创建索引
python elasticSearchSettingVector.py

# 启动后端服务
python contractApi.py
```

### 前端安装

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 开发模式启动
npm run dev

# 或构建生产版本
npm run build
```

## 📖 API 文档

### 主要接口

#### 文档上传
```http
POST /upload
Content-Type: multipart/form-data

file: PDF文件
```

#### 文档搜索
```http
POST /search
Content-Type: application/json

{
  "query": "搜索关键词",
  "size": 10
}
```

#### 文档删除
```http
DELETE /document/delete
Content-Type: application/json

{
  "filename": "文档名称.pdf"
}
```

#### 获取文档列表
```http
GET /documents
```

#### 健康检查
```http
GET /health
```

更多详细的 API 文档请访问：http://localhost:8006/docs

## 📁 项目结构

```
contract-search-system/
├── backend/                    # 后端代码
│   ├── contractApi.py         # 主 API 服务
│   ├── pdfToElasticSearch.py  # PDF 处理和索引
│   ├── elasticSearchSearch.py # 搜索功能
│   ├── elasticSearchDelete.py # 删除功能
│   ├── requirements.txt       # Python 依赖
│   └── ...
├── frontend/                   # 前端代码
│   ├── src/                   # 源代码
│   ├── public/                # 静态资源
│   ├── package.json           # Node.js 依赖
│   └── ...
├── start.sh                   # 启动脚本
├── stop.sh                    # 停止脚本
├── .gitignore                 # Git 忽略文件
└── README.md                  # 项目文档
```

## 🔍 使用说明

### 1. 上传文档
- 点击"上传文档"按钮
- 选择 PDF 格式的合同文件
- 系统会自动提取文本并建立索引

### 2. 搜索文档
- 在搜索框中输入关键词
- 系统会返回相关的文档片段
- 支持模糊搜索和语义搜索

### 3. 管理文档
- 查看已上传的文档列表
- 删除不需要的文档
- 下载原始文档

## ⚙️ 配置说明

### Elasticsearch 配置
- 默认地址：`http://localhost:9200`
- 索引名称：`contracts_vector`
- 向量维度：384（sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2）

### 服务端口
- 后端 API：8006
- 前端开发服务：5173
- Elasticsearch：9200

### 文件存储
- 上传的 PDF 文件存储在：`uploaded_contracts/`
- 日志文件存储在：`logs/`

## 🛠️ 开发指南

### 后端开发
```bash
cd backend
source contract_env/bin/activate
python contractApi.py
```

### 前端开发
```bash
cd frontend
npm run dev
```

### 添加新功能
1. 后端：在 `contractApi.py` 中添加新的 API 端点
2. 前端：在 `src/` 目录下添加新的 Vue 组件
3. 测试：确保新功能与现有系统兼容

## 🐛 故障排除

### 常见问题

1. **Elasticsearch 连接失败**
   ```bash
   # 检查 Docker 容器状态
   docker ps
   
   # 重启 Elasticsearch
   docker restart es
   ```

2. **端口被占用**
   ```bash
   # 查看端口占用
   lsof -i :8006
   
   # 停止占用进程
   ./stop.sh
   ```

3. **依赖安装失败**
   ```bash
   # 更新 pip
   pip install --upgrade pip
   
   # 清理缓存
   pip cache purge
   ```

4. **前端构建失败**
   ```bash
   # 清理 node_modules
   rm -rf node_modules package-lock.json
   npm install
   ```

### 日志查看
```bash
# 后端日志
tail -f logs/backend.log

# 前端日志
tail -f logs/frontend.log
```

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 👥 作者

- **RookieRunboy** - *初始工作* - [RookieRunboy](https://github.com/RookieRunboy)

## 🙏 致谢

- [Elasticsearch](https://www.elastic.co/) - 强大的搜索引擎
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [sentence-transformers](https://www.sbert.net/) - 文本向量化库

---

如果这个项目对你有帮助，请给它一个 ⭐️！