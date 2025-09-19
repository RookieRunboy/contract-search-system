from elasticsearch import Elasticsearch

es = Elasticsearch(
    "http://localhost:9200",
    headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8"}
)

index_name = "contracts_vector"

if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)

es.indices.create(
    index=index_name,
    body={
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
                    "dims": 768,  # 如果你用的是 bge-base-zh，维度就是 768
                    "index": True,
                    "similarity": "cosine"  # 也可以是 l2_norm、dot_product，根据模型向量特性来选
                }
            }
        }
    }
)

