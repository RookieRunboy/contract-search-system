# 合同智能检索（本地与服务器部署指南）

本项目提供“向量检索 + 关键词检索”的混合检索能力，基于 Elasticsearch 索引文本与向量，后端以 FastAPI 形式对外暴露上传、搜索、删除等接口。默认完全本地运行，也可部署在服务器对内网提供服务。

## 功能概览
- PDF 上传与解析（页级拆分 + 向量化）
- 混合检索（向量召回 + 关键词匹配）
- 文档删除（按文件名或页码)
- 系统状态自检（Elasticsearch 信息）
- 一键联调脚本（本地/远程 API 的自检、上传、搜索、删除）

## 目录结构（节选）
- test_codes/contractApi.py：后端服务（FastAPI）
- test_codes/elasticSearchSettingVector.py：创建索引（contracts_vector）
- test_codes/pdfToElasticSearch.py：从 PDF 解析并写入 ES
- test_codes/elasticSearchDelete.py：删除逻辑（已支持文件名归一化）
- test_api_local.py：本地/远程 API 联调 CLI
- 合同检索技术说明/environment.yml：可选 Conda 环境文件

## 环境准备
- Python：建议 3.10+（已在 3.13 下验证运行）
- 依赖（最小集）：
  - elasticsearch>=8.11
  - fastapi
  - uvicorn
  - sentence-transformers
  - requests
  - 解析 PDF 相关（例如 PyMuPDF/pypdf 等，具体以代码/环境为准）
- 可选（通过 Conda 环境）：
  - 使用 合同检索技术说明/environment.yml 创建虚拟环境。
- 模型下载加速/离线：
  - 如需使用镜像，设置环境变量：HF_ENDPOINT（例：中国大陆可选多种镜像）。

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

## API 使用示例
- 上传 PDF（multipart/form-data）：
```bash
curl -X POST "http://localhost:8006/document/add" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./案例合同/示例.pdf"
```
- 搜索：
```bash
curl -G "http://localhost:8006/document/search" \
  --data-urlencode "query=银华基金" \
  --data-urlencode "top_k=3"
```
- 删除（按文件名）：
```bash
# 兼容多种格式：example、example.pdf、/path/example.pdf
curl -X DELETE "http://localhost:8006/document/delete?filename=example"
```

说明：入库时文档的 contractName 以“文件名不带扩展名”的形式存储；删除接口现已对传入的文件名做归一化，兼容传入 stem、带扩展名或包含路径。

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