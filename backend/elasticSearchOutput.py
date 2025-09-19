from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")
index_name = "contracts"
query = "黄越"

body = {
  "size": 3,
  "query": {
    "multi_match": {
      "query": query,
      "type": "best_fields",
      "fields": ["text.standard^3", "text.ngram"],
      "operator": "or",
      "fuzziness": "AUTO"
    }
  },
  "highlight": {
    "fields": {
      "text": {}
    }
  }
}


results = es.search(index=index_name, body=body)

for hit in results["hits"]["hits"]:
    source = hit["_source"]
    print(f"Score: {hit['_score']:.2f} | Contract: {source['contractName']} | Page: {source['pageId']}")
    print(source["text"])
    print("=" * 40)