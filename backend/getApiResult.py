from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch

from embedding_client import RemoteEmbeddingClient

app = FastAPI()

# 初始化远程向量服务
try:
    embedding_client = RemoteEmbeddingClient(model="bge-m3")
except Exception as exc:
    print(f"Embedding service初始化失败: {exc}")
    embedding_client = None

# Elasticsearch 连接
es = Elasticsearch("http://localhost:9200")
index_name = "contracts_unified"

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
        if embedding_client is None:
            raise RuntimeError("远程向量服务不可用，无法执行向量检索")

        # 生成查询向量
        vectors = embedding_client.embed(request.query_text)
        if not vectors:
            raise RuntimeError("向量服务返回空结果")
        query_vector = vectors[0]

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
