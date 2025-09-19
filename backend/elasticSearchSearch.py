import json
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer


class ElasticsearchVectorSearch:
    def __init__(
            self,
            es_host: str = "http://localhost:9200",
            index_name: str = "contracts_vector",
            model_name: str = "BAAI/bge-base-zh"
    ):
        """
        初始化Elasticsearch向量搜索类

        :param es_host: Elasticsearch服务器地址
        :param index_name: 索引名称
        :param model_name: 句向量模型名称
        """
        try:
            self.es = Elasticsearch(es_host)
            self.model = SentenceTransformer(model_name)
            self.index_name = index_name

            # 检查连接
            if not self.es.ping():
                raise ConnectionError("Elasticsearch连接失败")
        except Exception as e:
            print(f"初始化错误: {str(e)}")
            raise

    def search(
            self,
            query_text: str,
            top_k: int = 3,
            text_standard: int = 3,
            text_ngram: int = 1,
            vector_weight: float = 5.0,
            fuzziness: str = "AUTO"
    ) -> List[Dict[str, Any]]:
        # 构建检索字段（支持标准字段与 ngram 子字段的权重）
        text_fields: List[str] = []
        if isinstance(text_standard, (int, float)) and text_standard > 0:
            # 使用主字段 text 作为标准检索字段
            text_fields.append(f"text^{int(text_standard)}")
        if isinstance(text_ngram, (int, float)) and text_ngram > 0:
            # 使用 text.ngram 作为 ngram 检索字段
            text_fields.append(f"text.ngram^{int(text_ngram)}")
        # 兜底：若未提供有效权重，至少检索主字段
        if not text_fields:
            text_fields = ["text^1"]

        # 生成查询向量
        query_vector = self.model.encode(query_text).tolist()

        # 构建搜索体
        body = {
            "size": top_k,
            "query": {
                "function_score": {
                    "query": {
                        "multi_match": {
                            "query": query_text,
                            "type": "best_fields",
                            "fields": text_fields,
                            "operator": "or",
                            "fuzziness": fuzziness
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
                            "weight": vector_weight
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    # 高亮字段不应包含权重或脚本字段，这里固定对原始 text 字段高亮
                    "text": {}
                }
            }
        }

        # 执行搜索
        try:
            results = self.es.search(index=self.index_name, body=body)
            return self._process_results(results)
        except Exception as e:
            print(f"搜索错误: {str(e)}")
            return []

    def index_document_chunks(self, chunks: List[Dict], filename: str):
        """
        将文档块索引到Elasticsearch
        
        :param chunks: 文档块列表
        :param filename: 文件名
        """
        try:
            for chunk in chunks:
                # 生成文档向量
                text_vector = self.model.encode(chunk['content']).tolist()
                
                # 构建文档
                doc = {
                    "contractName": filename,
                    "pageId": chunk['page_number'],
                    "text": chunk['content'],
                    "text_vector": text_vector
                }
                
                # 索引文档
                doc_id = f"{filename}_{chunk['chunk_id']}"
                self.es.index(
                    index=self.index_name,
                    id=doc_id,
                    body=doc
                )
            
            # 刷新索引
            self.es.indices.refresh(index=self.index_name)
            print(f"成功索引文档 {filename}，共 {len(chunks)} 个块")
            
        except Exception as e:
            print(f"索引文档失败: {str(e)}")
            raise
    
    def _process_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        处理搜索结果

        :param results: Elasticsearch原始搜索结果
        :return: 处理后的结果列表
        """
        processed_results = []
        for hit in results["hits"]["hits"]:
            result = {
                "score": hit["_score"],
                "contract_name": hit["_source"]["contractName"],
                "page_id": hit["_source"]["pageId"],
                "text": hit["_source"]["text"],
                "highlights": hit.get("highlight", {})
            }
            processed_results.append(result)
        return processed_results


if __name__ == "__main__":
    try:
        # 创建搜索实例
        searcher = ElasticsearchVectorSearch()

        # 执行搜索
        query_text = "银华基金管理股份有限公司"
        results = searcher.search(query_text)

        # 打印结果
        print(json.dumps(results, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"搜索异常: {str(e)}")