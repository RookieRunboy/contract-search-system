# 判断是否正确插入了索引与合同
import elasticsearch
import numpy as np

print("Elasticsearch Python client version:", elasticsearch.__version__)
print("NumPy version:", np.__version__)
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")
index_name = "contracts_vector"

exists = es.indices.exists(index=index_name)
print(f"索引 '{index_name}' 是否存在：", exists)
count = es.count(index=index_name)['count']
print(f"索引 '{index_name}' 中的文档数量：{count}")

