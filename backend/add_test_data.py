#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from elasticsearch import Elasticsearch

def add_test_data():
    """添加测试数据到Elasticsearch索引"""
    es = Elasticsearch(
        'http://localhost:9200',
        headers={'Accept': 'application/vnd.elasticsearch+json; compatible-with=8'}
    )
    
    # 添加测试数据
    test_docs = [
        {
            'contractName': '测试合同1.pdf',
            'pageId': 1,
            'text': '本合同为房屋租赁合同，甲方为出租人，乙方为承租人。租赁期限为一年，月租金为5000元。',
            'text_vector': [0.1] * 1024
        },
        {
            'contractName': '测试合同2.pdf', 
            'pageId': 1,
            'text': '劳动合同约定工作时间为每周40小时，试用期为3个月，基本工资为8000元每月。',
            'text_vector': [0.2] * 1024
        }
    ]
    
    for i, doc in enumerate(test_docs):
        result = es.index(index='contracts_vector', id=i+1, body=doc)
        print(f"添加文档 {i+1}: {result['result']}")
        
    print('测试数据添加成功')
    
    # 验证数据
    count = es.count(index='contracts_vector')
    print(f"索引中共有 {count['count']} 个文档")

if __name__ == '__main__':
    add_test_data()
