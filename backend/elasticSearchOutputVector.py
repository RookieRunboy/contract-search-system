from elasticsearch import Elasticsearch
import numpy as np

from embedding_client import RemoteEmbeddingClient

es = Elasticsearch("http://localhost:9200")
index_name = "contracts_unified"
query_text = "银华基金管理股份有限公司"

# 加载远程中文向量模型
embedding_client = RemoteEmbeddingClient(model="bge-m3")
vector_results = embedding_client.embed(query_text)
if not vector_results:
    raise RuntimeError("远程向量服务返回空结果")
query_vector = vector_results[0]  # 转为列表格式，方便JSON序列化

body = {
    "size": 3,
    "query": {
        "function_score": {
            "query": {
                "multi_match": {
                    "query": query_text,
                    "type": "best_fields",
                    "fields": ["text.standard^3", "text.ngram"],
                    "operator": "or",
                    "fuzziness": "AUTO"
                }
            },
            "boost_mode": "sum",  # 文本分数和向量分数相加
            "functions": [
                {
                    "script_score": {
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'text_vector') + 1.0",
                            "params": {
                                "query_vector": query_vector
                            }
                        }
                    },
                    "weight": 5  # 你可以调节向量权重
                }
            ]
        }
    },
    "highlight": {
        "fields": {
            "text.standard": {},
            "text.ngram": {}
        }
    }
}

results = es.search(index=index_name, body=body)

for hit in results["hits"]["hits"]:
    source = hit["_source"]
    print(f"Score: {hit['_score']:.2f} | Contract: {source['contractName']} | Page: {source['pageId']}")
    print(source["text"])
    print("=" * 40)

