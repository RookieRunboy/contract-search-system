import argparse

from elasticsearch import Elasticsearch


INDEX_NAME = "contracts_unified"
VECTOR_DIMENSION = 1024

UNIFIED_MAPPING = {
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
            "contractName": {"type": "keyword"},
            "pageId": {"type": "integer"},
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
                "dims": VECTOR_DIMENSION,
                "index": True,
                "similarity": "cosine"
            },
            "document_metadata": {
                "properties": {
                    "party_a": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "party_b": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "contract_type": {"type": "keyword"},
                    "contract_amount": {"type": "double"},
                    "signing_date": {"type": "date"},
                    "project_description": {"type": "text"},
                    "positions": {"type": "text"},
                    "personnel_list": {"type": "text"},
                    "extracted_at": {"type": "date"},
                    "metadata_vector": {
                        "type": "dense_vector",
                        "dims": VECTOR_DIMENSION,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            },
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
            "file_size": {"type": "long"},
            "total_pages": {"type": "integer"},
            "doc_type": {"type": "keyword"}
        }
    }
}


def create_index(force: bool = False) -> None:
    es = Elasticsearch(
        "http://localhost:9200",
        headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8"}
    )

    index_exists = es.indices.exists(index=INDEX_NAME)
    if index_exists:
        if not force:
            print(f"索引 {INDEX_NAME} 已存在，跳过创建。（使用 --force 可强制重建）")
            return
        es.indices.delete(index=INDEX_NAME)
        print(f"已删除现有索引: {INDEX_NAME}")

    es.indices.create(index=INDEX_NAME, body=UNIFIED_MAPPING)

    print(f"=== 成功创建统一索引: {INDEX_NAME} ===")
    print()
    print("索引特性:")
    print("1. 数据一致性：文档内容和元数据在同一索引中")
    print("2. 查询简化：单次查询获得完整信息")
    print("3. 原子操作：元数据更新和文档更新同步")
    print("4. 避免冗余：元数据只在第一页存储")
    print("5. 支持复合查询：可按元数据+内容组合搜索")
    print()
    print("设计要点:")
    print("- document_metadata只在pageId=1的文档中存储")
    print("- 其他页面的document_metadata为null，节省存储")
    print("- 支持元数据提取状态跟踪")
    print("- 保持向量搜索和文本搜索能力")
    print()
    print("示例查询场景:")
    print("1. 按甲方搜索：document_metadata.party_a.keyword:'甲方公司'")
    print("2. 按金额范围：document_metadata.contract_amount:[100000 TO 2000000]")
    print("3. 复合查询：甲方+内容关键词组合搜索")
    print("4. 元数据聚合：按合同类型、甲方等维度统计")
    print()
    print("索引创建完成！")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="创建或重建统一的合同索引")
    parser.add_argument("--force", action="store_true", help="强制删除并重建索引")
    args = parser.parse_args()
    create_index(force=args.force)
