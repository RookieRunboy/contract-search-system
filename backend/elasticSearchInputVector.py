import json
import os
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from sentence_transformers import SentenceTransformer

# 初始化 ES
es = Elasticsearch("http://localhost:9200")
index_name = "contracts_vector"

# 加载 bge-base-zh 模型（CPU 环境可运行）
model = SentenceTransformer("BAAI/bge-base-zh")

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
    vector = model.encode(text).tolist()  # 向量转换并转为 list（ES 要求）

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
