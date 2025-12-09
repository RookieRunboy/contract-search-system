#!/usr/bin/env python3
import requests
import json

# 测试搜索API
url = "http://localhost:8006/document/search"
params = {
    "query": "银华基金",
    "top_k": 3
}

response = requests.get(url, params=params)
result = response.json()

print("=== 搜索结果结构验证 ===")
print(f"状态码: {result['code']}")
print(f"消息: {result['message']}")
print(f"返回合同数量: {len(result['data'])}")

for i, contract in enumerate(result['data']):
    print(f"\n合同 {i+1}:")
    print(f"  合同名称: {contract['contract_name']}")
    print(f"  总分: {contract['score']:.2f}")
    print(f"  文档块数量: {len(contract['chunks'])}")
    
    for j, chunk in enumerate(contract['chunks'][:2]):  # 只显示前2个块
        print(f"    块 {j+1}: 分数={chunk['score']:.2f}, 页面={chunk['page_id']}")
        print(f"           文本预览: {chunk['text'][:50]}...")
