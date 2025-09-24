import json
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer


class ElasticsearchVectorSearch:
    def __init__(
            self,
            es_host: str = "http://localhost:9200",
            index_name: str = "contracts_unified",
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
            query_text: str = None,
            query_metadata: str = None,
            search_mode: str = "content",
            top_k: int = 3,
            text_standard: int = 3,
            text_ngram: int = 1,
            vector_weight: float = 5.0,
            metadata_weight: float = 3.0,
            fuzziness: str = "AUTO",
            amount_min: float = None,
            amount_max: float = None,
            date_start: str = None,
            date_end: str = None
    ) -> List[Dict[str, Any]]:
        """
        执行搜索
        
        Args:
            query_text: 内容查询文本
            query_metadata: 元数据查询文本
            search_mode: 搜索模式 ('content', 'metadata', 'hybrid')
            top_k: 返回结果数量
            text_standard: 标准文本字段权重
            text_ngram: ngram字段权重
            vector_weight: 向量搜索权重
            metadata_weight: 元数据搜索权重
            fuzziness: 模糊匹配程度
        
        Returns:
            搜索结果列表
        """
        if search_mode == "content":
            return self._search_content(query_text, top_k, text_standard, text_ngram, vector_weight, fuzziness, amount_min, amount_max, date_start, date_end)
        elif search_mode == "metadata":
            return self._search_metadata(query_metadata, top_k, metadata_weight, fuzziness, amount_min, amount_max, date_start, date_end)
        elif search_mode == "hybrid":
            return self._search_hybrid(query_text, query_metadata, top_k, text_standard, text_ngram, vector_weight, metadata_weight, fuzziness, amount_min, amount_max, date_start, date_end)
        else:
            raise ValueError(f"不支持的搜索模式: {search_mode}")
    
    def _search_content(
            self,
            query_text: str,
            top_k: int = 3,
            text_standard: int = 3,
            text_ngram: int = 1,
            vector_weight: float = 5.0,
            fuzziness: str = "AUTO",
            amount_min: float = None,
            amount_max: float = None,
            date_start: str = None,
            date_end: str = None
    ) -> List[Dict[str, Any]]:
        """
        内容搜索（原有逻辑）
        """
        if not query_text:
            return []
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

        # 构建筛选条件
        filter_clauses = []
        if amount_min is not None:
            filter_clauses.append({"range": {"document_metadata.contract_amount": {"gte": amount_min}}})
        if amount_max is not None:
            filter_clauses.append({"range": {"document_metadata.contract_amount": {"lte": amount_max}}})
        if date_start is not None:
            filter_clauses.append({"range": {"document_metadata.signing_date": {"gte": date_start}}})
        if date_end is not None:
            filter_clauses.append({"range": {"document_metadata.signing_date": {"lte": date_end}}})

        # 构建查询部分
        query_part = {
            "multi_match": {
                "query": query_text,
                "type": "best_fields",
                "fields": text_fields,
                "operator": "or",
                "fuzziness": fuzziness
            }
        }

        # 如果有筛选条件，使用bool查询包装
        if filter_clauses:
            query_part = {
                "bool": {
                    "must": [query_part],
                    "filter": filter_clauses
                }
            }

        # 构建搜索体
        body = {
            "size": top_k,
            "query": {
                "function_score": {
                    "query": query_part,
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
    
    def _search_metadata(
            self,
            query_metadata: str,
            top_k: int = 3,
            metadata_weight: float = 3.0,
            fuzziness: str = "AUTO",
            amount_min: float = None,
            amount_max: float = None,
            date_start: str = None,
            date_end: str = None
    ) -> List[Dict[str, Any]]:
        """
        元数据搜索
        """
        if not query_metadata:
            return []
        
        # 生成查询向量
        query_vector = self.model.encode(query_metadata).tolist()
        
        # 构建元数据字段搜索
        metadata_fields = [
            f"document_metadata.party_a^{metadata_weight}",
            f"document_metadata.party_b^{metadata_weight}",
            f"document_metadata.project_description^{metadata_weight * 0.8}",
            f"document_metadata.contract_type^{metadata_weight * 0.7}",
            f"document_metadata.positions^{metadata_weight * 0.6}",
            f"document_metadata.personnel_list^{metadata_weight * 0.6}"
        ]
        
        # 构建筛选条件
        filter_clauses = []
        if amount_min is not None:
            filter_clauses.append({"range": {"document_metadata.contract_amount": {"gte": amount_min}}})
        if amount_max is not None:
            filter_clauses.append({"range": {"document_metadata.contract_amount": {"lte": amount_max}}})
        if date_start is not None:
            filter_clauses.append({"range": {"document_metadata.signing_date": {"gte": date_start}}})
        if date_end is not None:
            filter_clauses.append({"range": {"document_metadata.signing_date": {"lte": date_end}}})
        
        # 构建查询部分的must条件
        must_clauses = [
            {"term": {"pageId": 1}},  # 只搜索第一页（包含元数据）
            {
                "multi_match": {
                    "query": query_metadata,
                    "type": "best_fields",
                    "fields": metadata_fields,
                    "operator": "or",
                    "fuzziness": fuzziness
                }
            }
        ]
        
        # 构建查询部分
        query_part = {
            "bool": {
                "must": must_clauses
            }
        }
        
        # 如果有筛选条件，添加到bool查询中
        if filter_clauses:
            query_part["bool"]["filter"] = filter_clauses
        
        # 构建搜索体
        body = {
            "size": top_k,
            "query": {
                "function_score": {
                    "query": query_part,
                    "boost_mode": "sum",
                    "functions": [
                        {
                            "script_score": {
                                "script": {
                                    "source": """
                                        if (doc['document_metadata.metadata_vector'].size() > 0) {
                                            return cosineSimilarity(params.query_vector, 'document_metadata.metadata_vector') + 1.0;
                                        } else {
                                            return 1.0;
                                        }
                                    """,
                                    "params": {
                                        "query_vector": query_vector
                                    }
                                }
                            },
                            "weight": metadata_weight
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "document_metadata.party_a": {},
                    "document_metadata.party_b": {},
                    "document_metadata.project_description": {},
                    "document_metadata.contract_type": {},
                    "document_metadata.positions": {},
                    "document_metadata.personnel_list": {}
                }
            }
        }
        
        # 执行搜索
        try:
            results = self.es.search(index=self.index_name, body=body)
            return self._process_metadata_results(results)
        except Exception as e:
            print(f"元数据搜索错误: {str(e)}")
            return []
    
    def _search_hybrid(
            self,
            query_text: str,
            query_metadata: str,
            top_k: int = 3,
            text_standard: int = 3,
            text_ngram: int = 1,
            vector_weight: float = 5.0,
            metadata_weight: float = 3.0,
            fuzziness: str = "AUTO",
            amount_min: float = None,
            amount_max: float = None,
            date_start: str = None,
            date_end: str = None
    ) -> List[Dict[str, Any]]:
        """
        混合搜索（内容 + 元数据）
        """
        content_results = []
        metadata_results = []
        
        # 执行内容搜索
        if query_text:
            content_results = self._search_content(query_text, top_k * 2, text_standard, text_ngram, vector_weight, fuzziness, amount_min, amount_max, date_start, date_end)
        
        # 执行元数据搜索
        if query_metadata:
            metadata_results = self._search_metadata(query_metadata, top_k * 2, metadata_weight, fuzziness, amount_min, amount_max, date_start, date_end)
        
        # 合并和重新排序结果
        return self._merge_results(content_results, metadata_results, top_k)
    
    def _merge_results(
            self,
            content_results: List[Dict[str, Any]],
            metadata_results: List[Dict[str, Any]],
            top_k: int
    ) -> List[Dict[str, Any]]:
        """
        合并内容搜索和元数据搜索结果
        """
        # 使用合同名称作为键来合并结果
        merged_dict = {}
        
        # 处理内容搜索结果
        for result in content_results:
            contract_name = result['contract_name']
            if contract_name not in merged_dict:
                merged_dict[contract_name] = {
                    'contract_name': contract_name,
                    'content_score': result['score'],
                    'metadata_score': 0,
                    'combined_score': result['score'],
                    'content_pages': [],
                    'metadata_info': None,
                    'highlights': result.get('highlights', {})
                }
            
            merged_dict[contract_name]['content_pages'].append({
                'page_id': result['page_id'],
                'text': result['text'],
                'score': result['score']
            })
        
        # 处理元数据搜索结果
        for result in metadata_results:
            contract_name = result['contract_name']
            if contract_name not in merged_dict:
                merged_dict[contract_name] = {
                    'contract_name': contract_name,
                    'content_score': 0,
                    'metadata_score': result['score'],
                    'combined_score': result['score'],
                    'content_pages': [],
                    'metadata_info': result.get('metadata_info'),
                    'highlights': result.get('highlights', {})
                }
            else:
                merged_dict[contract_name]['metadata_score'] = result['score']
                merged_dict[contract_name]['combined_score'] += result['score']
                merged_dict[contract_name]['metadata_info'] = result.get('metadata_info')
                # 合并高亮信息
                merged_dict[contract_name]['highlights'].update(result.get('highlights', {}))
        
        # 按综合得分排序并返回前top_k个结果
        sorted_results = sorted(
            merged_dict.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )
        
        return sorted_results[:top_k]
    
    def _process_metadata_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        处理元数据搜索结果
        """
        processed_results = []
        for hit in results["hits"]["hits"]:
            metadata_info = hit["_source"].get("document_metadata", {})
            result = {
                "score": hit["_score"],
                "contract_name": hit["_source"]["contractName"],
                "page_id": hit["_source"]["pageId"],
                "text": hit["_source"]["text"],
                "metadata_info": metadata_info,
                "highlights": hit.get("highlight", {})
            }
            processed_results.append(result)
        return processed_results

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
