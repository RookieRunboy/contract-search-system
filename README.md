# 合同智能检索系统

## 项目概述

本项目是一个基于AI的智能合同检索系统，旨在提供高效、精准的合同文档管理和检索功能。系统采用前后端分离架构，前端负责用户交互，后端提供核心的文档处理、索引和检索服务。

## 主要功能

- **合同上传**: 支持上传PDF格式的合同文档。
- **智能检索**: 基于自然语言处理和向量搜索技术，实现对合同内容的精准语义检索。
- **文档管理**: 提供已上传合同的列表、查看和管理功能。
- **元数据提取**: 自动从合同中提取关键元数据，如合同名称、签署日期等。

## 技术栈

### 前端

- **React**: 用于构建用户界面的JavaScript库。
- **TypeScript**: 为JavaScript添加了静态类型。
- **Ant Design**: 一套优秀的企业级UI设计语言和React组件库。
- **Vite**: 新一代的前端构建工具，提供极速的开发体验。
- **axios**: 用于处理与后端API的HTTP通信。
- **react-router-dom**: 为React应用提供路由功能。
- **react-highlight-words**: 用于在文本中高亮显示关键字。
- **dayjs**: 一个轻量级的处理时间和日期的JavaScript库。

### 后端

- **Python**: 作为后端开发的主要语言。
- **FastAPI**: 一个现代、快速（高性能）的web框架，用于构建API。
- **Elasticsearch**: 一个强大的开源搜索引擎，用于存储、搜索和分析大量数据。
- **Sentence-Transformers**: 一个Python框架，用于计算句子和文本的嵌入向量。
- **Uvicorn**: 一个闪电般快速的ASGI服务器。
- **PyPDF2**: 用于处理PDF文件的Python库。
- **python-multipart**: 用于处理multipart/form-data请求的Python库。
- **requests**: 一个简单而优雅的HTTP库。

## 项目架构

系统采用经典的前后端分离架构：

1.  **前端 (Client)**: 用户通过浏览器访问的单页应用（SPA）。它负责提供用户界面，让用户可以上传文档和执行搜索操作。
2.  **后端 (Server)**: 作为系统的核心，处理所有业务逻辑。它接收前端的请求，处理PDF文档，将其内容和向量表示存入Elasticsearch，并响应搜索查询。
3.  **数据存储 (Data Store)**: Elasticsearch被用作主数据存储和搜索引擎。它不仅存储合同的文本内容，还存储了用于语义搜索的向量嵌入。

## 安装与启动

### 环境准备

- Node.js (v16或更高版本)
- Python (v3.8或更高版本)
- Elasticsearch (v8.x)


### 快速启动
在根目录下
    ```bash
    ./start.sh
    ```
本地调试
    ```bash
    ./startest.sh
    ```
### 传统启动
#### 后端启动

1.  进入 `backend` 目录:
    ```bash
    cd backend
    ```

2.  安装Python依赖:
    ```bash
    pip install -r requirements.txt
    ```

3.  启动后端服务:
    ```bash
    uvicorn contractApi:app --reload
    ```
    服务将在 `http://127.0.0.1:8000` 上运行。

#### 前端启动

1.  进入 `frontend` 目录:
    ```bash
    cd frontend
    ```

2.  安装Node.js依赖:
    ```bash
    npm install
    ```

3.  启动前端开发服务器:
    ```bash
    npm run dev
    ```
    应用将在 `http://localhost:5173` 上可用。

## API 端点

后端服务提供以下主要API端点：

- `POST /document/add`: 上传一个新的合同文档。
- `GET /document/list`: 获取所有已上传文档的列表。
- `POST /document/search`: 对合同进行搜索。
- `DELETE /document/delete`: 删除一个指定的合同。

详细的API文档可以在后端服务启动后访问 `http://127.0.0.1:8000/docs` 查看。
