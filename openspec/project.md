# 项目上下文

## 概览
- 名称：合同智能检索系统（Contract Search System）
- 目标：通过 AI 能力完成合同的导入、语义检索与管理，提升 PDF 合同的查找效率。
- 架构：React/Vite 前端 + FastAPI 后端，借助 Elasticsearch 存储文本及向量嵌入。

## 技术栈
### 前端
- React 18、TypeScript、Vite 构建
- Ant Design 组件库、react-router-dom 路由、axios 调用后端
- 常用工具：react-highlight-words、dayjs、classnames

### 后端
- Python 3.8+，核心框架为 FastAPI + Uvicorn
- Sentence-Transformers 生成语义向量
- PyPDF2、python-multipart 负责 PDF 解析与上传处理
- requests 用于向外部服务发起 HTTP 请求

### 数据与基础设施
- Elasticsearch 8.x 作为合同文本、元数据及 ANN/语义搜索的主存储
- 原始上传文件保存在 `backend/uploaded_contracts/`
- `CONTRACT_API_KEY` 环境变量用于 LLM 相关的元数据/问答能力

## 关键工作流
- 一键启动：`./start.sh`（自动检查依赖并启动前后端）
- 后端开发：`python -m venv contract_env && source contract_env/bin/activate && pip install -r backend/requirements.txt`，运行 `uvicorn contractApi:app --host 0.0.0.0 --port 8006 --reload`
- 前端开发：`npm install --prefix frontend` 后执行 `npm run dev --prefix frontend`
- 生产构建：`npm run build --prefix frontend`

## 编码规范
- 后端：遵循 PEP 8，4 空格缩进，函数使用 snake_case，类名 PascalCase，FastAPI 模型明确类型注解，有条件时使用 `black`/`ruff` 格式化
- 前端：2 空格缩进，函数式组件，工具函数 camelCase，共享类型放在 `frontend/src/types`，提交前 `npm run lint --prefix frontend`
- 变更需聚焦，不要提交 `logs/`、`output/` 等生成物

## 测试要求
- 后端冒烟：`python backend/test_api.py`、`python backend/test_search.py`
- 端到端：`python test_api_local.py --check`
- 测试需覆盖使用 `backend/uploaded_contracts/` 或 `案例合同/` 的 Elasticsearch 查询

## 安全与运维
- 不要提交真实 API Key 或私密合同，所有密钥通过 `.env` 或系统环境变量注入
- 说明如何获取敏感配置，但不要写入版本库
- 上传文件与日志属于一次性产物，保持清理并确保在 `.gitignore` 中

## 业务要点
- 核心流程：合同上传 → 文本/向量抽取 → Elasticsearch 建索引 → 语义检索与结果高亮
- UI 需呈现：上传列表、搜索结果及其高亮片段、关键元数据（合同名、签署日期、甲乙方等）
