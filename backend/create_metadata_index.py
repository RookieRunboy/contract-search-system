from elasticsearch import Elasticsearch

es = Elasticsearch(
    "http://localhost:9200",
    headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8"}
)

index_name = "contract_metadata"

# 如果索引已存在，先删除
if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)
    print(f"已删除现有索引: {index_name}")

# 创建新的元数据索引，只包含6个必要字段
es.indices.create(
    index=index_name,
    body={
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "filename": {
                    "type": "keyword"
                },
                "metadata": {
                    "properties": {
                        "customer_name": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword"
                                }
                            }
                        },
                        "our_entity": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword"
                                }
                            }
                        },
                        "customer_category_level1": {
                            "type": "keyword"
                        },
                        "customer_category_level2": {
                            "type": "keyword"
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
                        }
                    }
                },
                "updated_at": {
                    "type": "date"
                },
                "doc_type": {
                    "type": "keyword"
                }
            }
        }
    }
)

print(f"成功创建元数据索引: {index_name}")
print("索引映射包含主要的元数据字段：")
print("- customer_name (客户名称)")
print("- our_entity (中软国际实体)")
print("- customer_category_level1 (客户分类一级)")
print("- customer_category_level2 (客户分类二级)")
print("- contract_type (合同方向，保留兼容)")
print("- contract_amount (合同金额)")
print("- project_description (项目描述)")
print("- positions (岗位)")
print("- personnel_list (人员清单)")
