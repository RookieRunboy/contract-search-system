import requests

# 获取所有文档
response = requests.get('http://localhost:8006/documents')
data = response.json()

print('文档列表检查:')
print('状态码:', response.status_code)
print('文档总数:', len(data['data']))
print()

# 显示所有文档信息
for i, doc in enumerate(data['data']):
    print(f'文档 {i+1}: {doc["name"]}')
    print(f'  分块数量: {doc["chunks_count"]}')
    print(f'  状态: {doc["status"]}')
    print()

# 测试搜索不同关键词
test_keywords = ['刘明', '华泰证券', '甲方', '乙方']

for keyword in test_keywords:
    print(f'\n搜索关键词: "{keyword}"')
    search_response = requests.get(f'http://localhost:8006/search?query={keyword}&top_k=5')
    search_data = search_response.json()
    
    if search_data['data']:
        print(f'  找到 {len(search_data["data"])} 个结果')
        for j, result in enumerate(search_data['data'][:2]):  # 只显示前2个结果
            print(f'    结果 {j+1}: 合同={result["contract_name"]}, 页面={result["page_id"]}, 评分={result["score"]:.2f}')
            # 检查文本中是否真的包含关键词
            if keyword in result['text']:
                print(f'      ✓ 文本中确实包含"{keyword}"')
            else:
                print(f'      ✗ 文本中不包含"{keyword}"，可能是模糊匹配')
    else:
        print('  没有找到结果')

print('\n分析结论:')
print('1. 搜索"刘明"返回了结果，但返回的文档文本中并不包含"刘明"')
print('2. 这可能是因为:')
print('   - Elasticsearch的模糊匹配算法')
print('   - 索引中的数据与实际显示的文本不一致')
print('   - 搜索算法配置问题')