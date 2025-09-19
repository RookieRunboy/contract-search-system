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
print("索引映射只包含6个必要的元数据字段：")
print("- party_a (甲方)")
print("- party_b (乙方)")
print("- contract_type (合同类型)")
print("- contract_amount (合同金额)")
print("- project_description (项目描述)")
print("- positions (岗位)")
print("- personnel_list (人员清单)")