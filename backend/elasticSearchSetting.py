from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

index_name = "contracts"

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
                        },
                    },
                    "analyzer": "standard",
                    "search_analyzer": "standard"
                }
            }
        }
    }
)
