from elasticsearch import Elasticsearch
from elasticsearch import helpers
from pathlib import Path

class get_document_by_filename:
    def __init__(self, es_host="http://localhost:9200", index_name="contracts_vector"):
        self.es = Elasticsearch(es_host)
        self.index_name = index_name
    
    def _normalize_filename(self, filename: str) -> str:
        """
        规范化文件名：
        - 支持传入 example 或 example.pdf 或包含路径的 /path/example.pdf
        - 实际索引中的 contractName 存的是文件名的"无扩展名"部分
        """
        try:
            name = Path(filename).name  # 去掉路径
            stem = Path(name).stem      # 去掉扩展名
            return stem
        except Exception:
            return filename
    
    def get_document_text(self, filename):
        """
        根据文件名从Elasticsearch获取完整的文档文本内容
        """
        try:
            # 检查索引是否存在
            if not self.es.indices.exists(index=self.index_name):
                print(f"索引 {self.index_name} 不存在")
                return None
            
            # 规范化文件名
            normalized_filename = self._normalize_filename(filename)
            print(f"原始文件名: {filename}, 规范化后: {normalized_filename}")
            
            # 构建查询，根据contractName字段匹配文件名
            # 使用match查询而不是term查询，以更好地处理中文字符
            query = {
                "query": {
                    "match": {
                        "contractName": normalized_filename
                    }
                },
                "sort": [
                    {"pageId": {"order": "asc"}}
                ],
                "_source": ["text", "pageId"]
            }
            
            # 使用scan获取所有匹配的文档
            hits = list(helpers.scan(
                self.es,
                index=self.index_name,
                query=query,
                size=200,
                preserve_order=True
            ))
            
            if not hits:
                return None
            
            # 按页面顺序拼接所有文本内容
            full_text = ""
            for hit in hits:
                source = hit.get("_source", {})
                text = source.get("text", "")
                if text:
                    full_text += text + "\n"
            
            return full_text.strip()
            
        except Exception as e:
            print(f"获取文档文本失败: {str(e)}")
            return None

# 原有的搜索代码（已注释，避免在导入时执行）
# es = Elasticsearch("http://localhost:9200")
# index_name = "contracts"
# query = "黄越"

# body = {
#   "size": 3,
#   "query": {
#     "multi_match": {
#       "query": query,
#       "type": "best_fields",
#       "fields": ["text.standard^3", "text.ngram"],
#       "operator": "or",
#       "fuzziness": "AUTO"
#     }
#   },
#   "highlight": {
#     "fields": {
#       "text": {}
#     }
#   }
# }

# results = es.search(index=index_name, body=body)

# for hit in results["hits"]["hits"]:
#     source = hit["_source"]
#     print(f"Score: {hit['_score']:.2f} | Contract: {source['contractName']} | Page: {source['pageId']}")
#     print(source["text"])
#     print("=" * 40)