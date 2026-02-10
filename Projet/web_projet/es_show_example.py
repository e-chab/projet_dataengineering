from elasticsearch import Elasticsearch

# Connexion à Elasticsearch (adapter l'URL si besoin)
es = Elasticsearch('http://localhost:9200')

# Récupère un exemple de document de l'index ikea_reviews
def print_example_doc():
    res = es.search(index="ikea_reviews", size=1)
    if res['hits']['hits']:
        import json
        print(json.dumps(res['hits']['hits'][0]['_source'], indent=2, ensure_ascii=False))
    else:
        print("Aucun document trouvé dans l'index ikea_reviews.")

if __name__ == "__main__":
    print_example_doc()
