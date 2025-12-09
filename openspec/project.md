# 项目概览

## 概述
- 名称：合同智能检索系统（Contract Search System）
- 目标：通过 AI 提升合同文本的上传、解析、检索效率，支持搜索 PDF 合同。
- 架构：React/Vite 前端 + FastAPI 后端，Elasticsearch 存储文本和向量。

## 技术栈
### 前端
- React 18、TypeScript、Vite
- Ant Design 组件库、react-router-dom 路由、axios 请求
- 其他：react-highlight-words、dayjs、classnames

### 后端
- Python 3.8+，框架 FastAPI + Uvicorn
- Sentence-Transformers 生成向量
- PyPDF2、python-multipart 处理 PDF、上传
- requests 调用外部 HTTP 服务

### 基础设施
- Elasticsearch 8.x 存储合同文本、元数据与 ANN/向量索引
- 原始上传文件位于 `backend/uploaded_contracts/`
- `CONTRACT_API_KEY` 提供 LLM 相关的元数据/问答能力

## 关键命令
- 一键启动：`./start.sh`
- 后端开发：`python -m venv contract_env && source contract_env/bin/activate && pip install -r backend/requirements.txt`，运行 `uvicorn contractApi:app --host 0.0.0.0 --port 8006 --reload`
- 前端开发：`npm install --prefix frontend`，启动 `npm run dev --prefix frontend`
- 构建前端：`npm run build --prefix frontend`

## 代码规范
- 后端：遵循 PEP 8，4 空格缩进，函数 snake_case，类 PascalCase，FastAPI 模型注明类型；有 formatter 时使用 `black`/`ruff`
- 前端：2 空格缩进，函数式组件，工具方法 camelCase，类型放在 `frontend/src/types`；提交前 `npm run lint --prefix frontend`
- 临时或生成文件不要提交到 `logs/`、`output/`

## 测试要求
- 后端单测：`python backend/test_api.py`、`python backend/test_search.py`
- 端到端：`python test_api_local.py --check`
- 索引/数据依赖：使用 `backend/uploaded_contracts/` 或 `案例合同/` 和 Elasticsearch 查询

## 安全与配置
- 不要提交真实 API Key、私密合同；通过 `.env` 或系统环境变量配置
- 说明如何获取敏感配置，但不要写入仓库
- 上传文件和日志属于一次性产物，确保 `.gitignore` 覆盖

## 业务要点
- 主要流程：合同上传 → 文本/元数据提取 → Elasticsearch 索引 → 搜索与结果展示
- UI 需覆盖：上传列表、搜索结果、契合片段、核心元数据（合同金额、签署日期、匹配度等）
