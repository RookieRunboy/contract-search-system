# 客户端测试服务器能否运行
import json

import requests
from pathlib import Path

def addtest():
    url = "http://172.16.5.31:8006/document/add"
    pdf_path = Path(r"D:\Personal\Desktop\2.pdf")
    with open(pdf_path, "rb") as f:
        files = {"file": (Path(pdf_path).name, f, "application/pdf")}
        response = requests.post(url, files=files)
    print(response.json())

def searchtest():
    url = "http://172.16.5.31:8006/document/search"
    params = {
        "query": "合同",
        "top_k": 5,
        "text_standard": 3,
        "text_ngram": 1,
        "vector_weight": 5.0,
        "fuzziness": "AUTO"
    }
    response = requests.get(url, params=params)
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

def deletetest():
    url = "http://172.16.5.31:8006/document/delete"
    params = {"filename": "2"}
    response = requests.delete(url, params=params)
    print(response.json())

if __name__ == "__main__":
    print("test")
    # addtest()
    # deletetest()
    searchtest()
