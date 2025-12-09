import requests

# 搜索刘明
response = requests.get('http://localhost:8006/search?query=刘明&top_k=20')
data = response.json()

print('搜索"刘明"的结果:')
print('状态码:', response.status_code)
print('总搜索结果数量:', len(data['data']))
print()

# 检查每个结果是否包含"刘明"
found_liuming = False
for i, result in enumerate(data['data']):
    if '刘明' in result['text']:
        print(f'找到包含"刘明"的文档 {i+1}:')
        print(f'  合同: {result["contract_name"]}')
        print(f'  页面: {result["page_id"]}')
        print(f'  评分: {result["score"]}')
        print(f'  文本片段: {result["text"][:300]}...')
        print()
        found_liuming = True

if not found_liuming:
    print('所有返回的文档都不包含"刘明"关键词')
    print()
    print('返回的文档详情:')
    for i, result in enumerate(data['data']):
        print(f'文档 {i+1}:')
        print(f'  合同: {result["contract_name"]}')
        print(f'  页面: {result["page_id"]}')
        print(f'  评分: {result["score"]}')
        print(f'  文本前100字: {result["text"][:100]}...')
        print()