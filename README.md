# 合同智能检索系统

一个基于 Elasticsearch 和 AI 向量搜索的智能合同检索系统，支持 PDF 文档上传、文本提取、向量化存储和智能搜索。

## 🚀 功能特性

- **智能文档上传**: 支持 PDF 格式合同文档上传
- **文本提取**: 自动提取 PDF 文档中的文本内容
- **向量化存储**: 使用 sentence-transformers 生成文本向量并存储到 Elasticsearch
- **混合搜索**: 结合传统文本搜索和向量相似度搜索
- **元数据提取**: 基于 LLM 的智能元数据提取（甲乙双方、合同金额、客户类型等）
- **现代化界面**: 基于 React + TypeScript 的响应式前端界面
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
- **React 18**: 现代化 JavaScript 框架
- **TypeScript**: 类型安全的 JavaScript
- **Vite**: 现代化构建工具
- **Ant Design**: React 组件库

### 基础设施
- **Docker**: Elasticsearch 容器化部署
- **Git**: 版本控制

## 📁 项目结构
```
contract-search-system/
├── backend/                    # 后端代码
│   ├── contractApi.py         # 主 API 服务
│   ├── llm_metadata_extractor.py # LLM 元数据提取
│   ├── pdfToElasticSearch.py  # PDF 处理和索引
│   ├── elasticSearchSearch.py # 搜索功能
│   ├── elasticSearchDelete.py # 删除功能
│   ├── requirements.txt       # Python 依赖
│   └── ...
├── frontend/                   # 前端代码
│   ├── src/                   # 源代码
│   │   ├── components/        # React 组件
│   │   ├── pages/            # 页面组件
│   │   ├── services/         # API 服务
│   │   └── types/            # TypeScript 类型定义
│   ├── public/                # 静态资源
│   ├── package.json           # Node.js 依赖
│   └── ...
├── start.sh                   # 启动脚本
├── stop.sh                    # 停止脚本
├── .gitignore                 # Git 忽略文件
└── README.md                  # 项目文档
```

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
- 启动 Elasticsearch Docker 容器
- 安装 Python 和 Node.js 依赖
- 创建 Elasticsearch 索引
- 启动后端 API 服务
- 构建并部署前端应用

### 3. 访问应用
启动完成后，可以通过以下地址访问：
- **前端应用**: http://localhost:5173
- **后端 API**: http://localhost:8007/docs
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

## 启动 Elasticsearch（Docker 推荐）
示例使用 8.13.4，单机模式、关闭安全认证：

```bash
docker run -d --name es \
  -p 9200:9200 \
  -e discovery.type=single-node \
  -e xpack.security.enabled=false \
  -e ES_JAVA_OPTS="-Xms2g -Xmx2g" \
  docker.elastic.co/elasticsearch/elasticsearch:8.13.4
```

启动后访问 http://localhost:9200 应返回 ES 信息。

## 创建索引（contracts_vector）
运行脚本创建索引并配置向量字段、分析器等：

```bash
python test_codes/elasticSearchSettingVector.py
```

成功后可在 ES 中看到 contracts_vector 索引。

## 启动后端服务（FastAPI）
两种方式任选其一：

- 直接运行脚本（项目中常用）：
```bash
python test_codes/contractApi.py
```
- 或使用 uvicorn 显式启动：
```bash
uvicorn test_codes.contractApi:app --host 0.0.0.0 --port 8006
```

启动后可访问：
- 文档/调试界面：http://localhost:8006/docs
- 系统自检：GET http://localhost:8006/system/elasticsearch

## 📖 API 文档

### 主要接口

#### 文档上传
```bash
POST /document/add
Content-Type: multipart/form-data

curl -X POST "http://localhost:8007/document/add" \
  -F "file=@./contract.pdf"
```

#### 文档搜索
```bash
POST /document/search
Content-Type: application/json

curl -X POST "http://localhost:8007/document/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "合同条款", "size": 10}'
```

#### 元数据提取
```bash
POST /document/extract-metadata?filename=contract.pdf

curl -X POST "http://localhost:8007/document/extract-metadata?filename=contract.pdf"
```

#### 文档删除
```bash
DELETE /document/delete?filename=contract.pdf

curl -X DELETE "http://localhost:8007/document/delete?filename=contract.pdf"
```

#### 获取文档列表
```bash
GET /documents

curl -X GET "http://localhost:8007/documents"
```

#### 健康检查
```bash
GET /health

curl -X GET "http://localhost:8007/health"
```

更多详细的 API 文档请访问：http://localhost:8007/docs

## 🔍 使用说明

### 1. 上传文档
- 点击"上传文档"按钮
- 选择 PDF 格式的合同文件
- 系统会自动提取文本并建立索引

### 2. 搜索文档
- 在搜索框中输入关键词
- 系统会返回相关的文档片段
- 支持模糊搜索和语义搜索

### 3. 元数据提取
- 在文档列表中点击"提取元数据"
- 系统会使用 LLM 自动提取合同的关键信息
- 包括甲乙双方、合同金额、客户类型等

### 4. 管理文档
- 查看已上传的文档列表
- 删除不需要的文档
- 下载原始文档

## ⚙️ 配置说明

### Elasticsearch 配置
- 默认地址：http://localhost:9200
- 索引名称：contracts_vector
- 向量维度：384（sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2）

### 服务端口
- 后端 API：8007
- 前端开发服务：5173
- Elasticsearch：9200

### 文件存储
- 上传的 PDF 文件存储在：backend/uploaded_contracts/
- 日志文件存储在：logs/

## 一键联调脚本（test_api_local.py）

本项目提供了一个用于本地/远程 API 联调的脚本：<mcfile name="test_api_local.py" path="/Users/runbo/Desktop/合同智能检索/test_api_local.py"></mcfile>

- 功能：自检后端与 ES、上传 PDF、搜索、删除（兼容不带扩展名/带扩展名/包含路径）
- 默认地址：脚本内置 BASE_URL= http://172.16.5.31:8006，可用 -u/--url 指定其他地址

### 常用示例（CLI 快速使用）

完整 CLI 参数见 <mcfile name="test_api_local.py" path="/Users/runbo/Desktop/合同智能检索/test_api_local.py"></mcfile> 或执行：

```
python test_api_local.py --help
```

- 默认烟雾测试（无参数时：自检 -> 上传示例PDF -> 搜索 -> 打印删除提示）
  - python test_api_local.py
- 后端/ES 自检
  - python test_api_local.py --check
  - python test_api_local.py -u http://localhost:8006 --check
  - python test_api_local.py -u http://172.16.5.31:8006 --check
- 上传 PDF（入库+向量化）
  - python test_api_local.py -u http://localhost:8006 -U "./案例合同/合同1.pdf" "./案例合同/合同2.pdf"
- 搜索（混合检索：向量+关键词）
  - python test_api_local.py -u http://localhost:8006 -q "银华基金" --top-k 5
- 删除（兼容文件名 stem/带扩展名/包含路径）
  - python test_api_local.py -u http://localhost:8006 -d 合同1
  - 或：python test_api_local.py -u http://localhost:8006 -d 合同1.pdf
  - 或：python test_api_local.py -u http://localhost:8006 -d "./案例合同/合同1.pdf"
- 一次删除多个文档
  - python test_api_local.py -u http://localhost:8006 -d 合同1 合同2.pdf 合同3
- 组合执行（自检 -> 上传 -> 搜索 -> 删除）
  - python test_api_local.py -u http://localhost:8006 --check -U "./a.pdf" "./b.pdf" -q "付款条款" --top-k 10 -d a b

> 提示：脚本默认请求超时已加长（上传600s、搜索60s），适合大 PDF/首次建模。

### 机器可读能力（推荐给大模型/自动化代理）

- 即时自描述输出：脚本支持 --spec 打印 JSON 能力清单，适合让智能体在新对话中快速发现与调用脚本能力。

```
python test_api_local.py --spec | jq .
```

- 静态能力文件：项目根目录提供 <mcfile name="actions.json" path="/Users/runbo/Desktop/合同智能检索/actions.json"></mcfile>，内容与 --spec 对齐，便于无需读取源码即可消费。

常见消费方式：
- 读取 actions.json，选择 action 与参数，拼装 HTTP 请求到后端 API；
- 或调用本脚本 CLI（例如通过子进程/终端执行），并根据退出码与标准输出进行编排；
- 与 API 文档（/docs 或 OpenAPI）搭配，可将 CLI 作为调试与批处理工具，共享一套后端。