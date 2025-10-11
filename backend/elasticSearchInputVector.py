import json
import os
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from embedding_client import RemoteEmbeddingClient

# 初始化 ES
es = Elasticsearch("http://localhost:9200")
index_name = "contracts_unified"

# 初始化远程向量服务
embedding_client = RemoteEmbeddingClient(model="bge-m3")

# 文件路径
file_path = r"/Users/runbo/Desktop/合同智能检索/output/contract_text.json"
contract_name = "sample_contract"

# 读取 JSON 页面数据
with open(file_path, "r", encoding="utf-8") as f:
    pages = json.load(f)

# 逐页构建 actions（含向量）
actions = []
for page in pages:
    text = page["text"]
    vector_results = embedding_client.embed(text)
    if not vector_results:
        raise RuntimeError("远程向量服务返回空结果")
    vector = vector_results[0]  # 向量转换并转为 list（ES 要求）

    actions.append({
        "_index": index_name,
        "_source": {
            "contractName": contract_name,
            "pageId": page["pageId"],
            "text": text,
            "text_vector": vector  # 加入向量字段
        }
    })

# 批量写入 ES
bulk(es, actions)
