from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import numpy as np
import torch

app = FastAPI()

# 使用NPU
try:
    device = torch.device('npu:7')
    print(f"Using NPU device: {device}")

    # 验证指定的NPU设备是否可用
    if not torch.npu.is_available():
        print("NPU is not available!")
        device = torch.device('cpu')

    # 加载向量模型，明确指定设备
    model = SentenceTransformer(
        "BAAI/bge-base-zh",
        device=str(device)
    )
except Exception as e:
    print(f"Error setting up NPU device: {e}")
    # 降级到CPU
    device = torch.device('cpu')
    model = SentenceTransformer(
        "BAAI/bge-base-zh",
        device='cpu'
    )

# Elasticsearch 连接
es = Elasticsearch("http://localhost:9200")
index_name = "contracts_vector"

# 请求体模型
class SearchRequest(BaseModel):
    query_text: str
    text_match_weight: float = 3.0  # 文本匹配权重
    vector_match_weight: float = 5.0  # 向量匹配权重
    fuzzy_match_weight: float = 2.0  # 模糊匹配权重
    size: int = 3  # 返回结果数量

@app.post("/search")
def semantic_search(request: SearchRequest):
    try:
        # 生成查询向量
        query_vector = model.encode(request.query_text).tolist()

        # 构建搜索体
        body = {
            "size": request.size,
            "query": {
                "function_score": {
                    "query": {
                        "multi_match": {
                            "query": request.query_text,
                            "type": "best_fields",
                            "fields": ["text.standard^3", "text.ngram"],
                            "operator": "or",
                            "fuzziness": "AUTO"
                        }
                    },
                    "boost_mode": "sum",
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
                            "weight": request.vector_match_weight
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

        # 执行搜索
        results = es.search(index=index_name, body=body)

        # 处理结果
        processed_results = []
        for hit in results["hits"]["hits"]:
            source = hit["_source"]
            processed_results.append({
                "score": hit['_score'],
                "contract_name": source['contractName'],
                "page_id": source['pageId'],
                "text": source["text"]
            })

        return {
            "total_hits": results["hits"]["total"]["value"],
            "results": processed_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 运行方式
# uvicorn your_file_name:app --reload
