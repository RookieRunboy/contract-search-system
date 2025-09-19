import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import os

es = Elasticsearch("http://localhost:9200")

index_name = "contracts"
file_path = r"D:\Cyc\MyWork\testFiles\output_llm\output_paddleocr\CIR500000220516017-银华基金信息系统技术开发服务合同-2022外包-银华基金管理股份有限公司-3263400-完整版.json"
contract_name = os.path.basename(file_path).replace('.json', '')

with open(file_path, "r", encoding="utf-8") as f:
    pages = json.load(f)

actions = [
    {
        "_index": index_name,
        "_source": {
            "contractName": contract_name,
            "pageId": page["pageId"],
            "text": page["text"]
        }
    }
    for page in pages
]

bulk(es, actions)
