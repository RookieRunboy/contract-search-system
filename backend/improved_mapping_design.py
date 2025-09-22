from elasticsearch import Elasticsearch

# 改进的统一mapping设计
# 将元数据字段直接集成到合同文档索引中

es = Elasticsearch(
    "http://localhost:9200",
    headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8"}
)

index_name = "contracts_unified"

# 统一的合同文档索引mapping
unified_mapping = {
    "settings": {
        "analysis": {
            "tokenizer": {
                "ngram_tokenizer": {
                    "type": "ngram",
                    "min_gram": 2,
                    "max_gram": 3,
                    "token_chars": ["letter", "digit"]
                }
            },
            "analyzer": {
                "ngram_analyzer": {
                    "type": "custom",
                    "tokenizer": "ngram_tokenizer"
                },
                "standard_analyzer": {
                    "type": "standard"
                }
            }
        }
    },
    "mappings": {
        "properties": {
            # 基础文档信息
            "contractName": {
                "type": "keyword"
            },
            "pageId": {
                "type": "integer"
            },
            "text": {
                "type": "text",
                "fields": {
                    "ngram": {
                        "type": "text",
                        "analyzer": "ngram_analyzer",
                        "search_analyzer": "standard"
                    },
                    "standard": {
                        "type": "text",
                        "analyzer": "standard"
                    }
                },
                "analyzer": "standard",
                "search_analyzer": "standard"
            },
            "text_vector": {
                "type": "dense_vector",
                "dims": 768,
                "index": True,
                "similarity": "cosine"
            },
            
            # 文档级别的元数据（只在第一页存储，避免冗余）
            "document_metadata": {
                "properties": {
                    "party_a": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "party_b": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "contract_type": {
                        "type": "keyword"
                    },
                    "contract_amount": {
                        "type": "double"
                    },
                    "project_description": {
                        "type": "text"
                    },
                    "positions": {
                        "type": "text"
                    },
                    "personnel_list": {
                        "type": "text"
                    },
                    "extracted_at": {
                        "type": "date"
                    },
                    "extraction_status": {
                        "type": "keyword",  # pending, completed, failed
                        "value": "pending"
                    }
                }
            },
            
            # 文档管理字段
            "created_at": {
                "type": "date"
            },
            "updated_at": {
                "type": "date"
            },
            "file_size": {
                "type": "long"
            },
            "total_pages": {
                "type": "integer"
            },
            
            # 标识字段
            "doc_type": {
                "type": "keyword"  # page_content, document_summary
            }
        }
    }
}

print("=== 改进的统一Mapping设计 ===")
print("\n优势分析：")
print("1. 数据一致性：文档内容和元数据在同一索引中")
print("2. 查询简化：单次查询获得完整信息")
print("3. 原子操作：元数据更新和文档更新同步")
print("4. 避免冗余：元数据只在第一页存储")
print("5. 支持复合查询：可按元数据+内容组合搜索")

print("\n设计要点：")
print("- document_metadata只在pageId=1的文档中存储")
print("- 其他页面的document_metadata为null，节省存储")
print("- 支持元数据提取状态跟踪")
print("- 保持向量搜索和文本搜索能力")

# 示例文档结构
example_doc_page1 = {
    "contractName": "sample_contract",
    "pageId": 1,
    "text": "合同第一页内容...",
    "text_vector": [0.1, 0.2, 0.3],  # 768维向量
    "document_metadata": {
        "party_a": "甲方公司",
        "party_b": "乙方公司", 
        "contract_type": "技术服务合同",
        "contract_amount": 1000000.0,
        "project_description": "系统开发项目",
        "positions": "技术经理、开发工程师",
        "personnel_list": "张三、李四",
        "extracted_at": "2024-01-15T10:00:00",
        "extraction_status": "completed"
    },
    "created_at": "2024-01-15T09:00:00",
    "updated_at": "2024-01-15T10:00:00",
    "file_size": 2048576,
    "total_pages": 10,
    "doc_type": "page_content"
}

example_doc_page2 = {
    "contractName": "sample_contract",
    "pageId": 2,
    "text": "合同第二页内容...",
    "text_vector": [0.4, 0.5, 0.6],
    "document_metadata": None,  # 其他页面不存储元数据
    "created_at": "2024-01-15T09:00:00",
    "updated_at": "2024-01-15T09:00:00",
    "file_size": 2048576,
    "total_pages": 10,
    "doc_type": "page_content"
}

print("\n示例查询场景：")
print("1. 按甲方搜索：document_metadata.party_a:'甲方公司'")
print("2. 按金额范围：document_metadata.contract_amount:[100000 TO 2000000]")
print("3. 复合查询：甲方+内容关键词组合搜索")
print("4. 元数据聚合：按合同类型、甲方等维度统计")