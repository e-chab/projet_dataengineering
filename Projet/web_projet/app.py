from flask import Flask, render_template, request
from pymongo import MongoClient
from elasticsearch import Elasticsearch
import os

app = Flask(__name__)

# Configuration MongoDB
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['ikea_db']
collection = db['products']

# Configuration Elasticsearch
ES_HOSTS = os.environ.get('ELASTICSEARCH_HOSTS', 'http://elasticsearch:9200')
es = Elasticsearch(ES_HOSTS)


# Dashboard landing page
@app.route('/')
def dashboard():
    return render_template('dashboard.html')


# Page 1: statistiques messages commerciaux
@app.route('/page1')
def index():
    categories = db.products.distinct('category_hierarchy.1')
    categories = [c for c in categories if c]
    categories.sort()

    # Prépare les labels et les comptes par catégorie
    from collections import defaultdict
    label_set = set()
    combined_label_set = set()
    # Dictionnaire : {cat: {label: count}}
    category_label_counts = defaultdict(lambda: defaultdict(int))

    for doc in db.products.find({"category_hierarchy.1": {"$in": categories}}):
        cat = doc.get('category_hierarchy', [None, None])[1]
        if not cat:
            continue
        messages = doc.get('commercial_message', [])
        # Ajout du label 'Réduction' si un message correspond à 'Réduction XX%'
        reduction_found = False
        reduction_label = 'Réduction'
        filtered_messages = []
        if isinstance(messages, list):
            for msg in messages:
                if isinstance(msg, str) and msg.strip().startswith('Réduction') and '%' in msg:
                    reduction_found = True
                else:
                    filtered_messages.append(msg)
            if reduction_found:
                label_set.add(reduction_label)
                category_label_counts[cat][reduction_label] += 1
            # Traite les autres messages normalement
            if len(filtered_messages) == 1:
                label = filtered_messages[0]
                label_set.add(label)
                category_label_counts[cat][label] += 1
            elif len(filtered_messages) == 2:
                msgs_sorted = sorted(filtered_messages)
                label = f'{msgs_sorted[0]} & {msgs_sorted[1]}'
                combined_label_set.add(label)
                category_label_counts[cat][label] += 1
        elif isinstance(messages, str):
            if messages.strip().startswith('Réduction') and '%' in messages:
                label_set.add(reduction_label)
                category_label_counts[cat][reduction_label] += 1
            else:
                label = messages
                label_set.add(label)
                category_label_counts[cat][label] += 1

    # Prépare les listes pour le frontend
    message_types = sorted(label_set)
    combined_labels = sorted(combined_label_set)
    data_counts = []
    for msg in message_types:
        data_counts.append([category_label_counts[cat].get(msg, 0) for cat in categories])
    combined_data_counts = []
    for label in combined_labels:
        combined_data_counts.append([category_label_counts[cat].get(label, 0) for cat in categories])

    # Données pour le camembert des réductions
    reduction_counts = defaultdict(int)
    # Cherche les messages qui commencent par "Réduction" et se terminent par "%"
    for doc in db.products.find({"commercial_message": {"$regex": "^Réduction \\d+%"}}):
        messages = doc.get('commercial_message', [])
        # Assure que 'messages' est une liste pour l'itération
        if not isinstance(messages, list):
            messages = [messages]
        for msg in messages:
            if isinstance(msg, str) and msg.strip().startswith('Réduction') and '%' in msg:
                reduction_counts[msg.strip()] += 1
    
    reduction_labels = sorted(reduction_counts.keys())
    reduction_data = [reduction_counts[label] for label in reduction_labels]

    return render_template('index.html', categories=categories, message_types=message_types, data_counts=data_counts, combined_labels=combined_labels, combined_data_counts=combined_data_counts, reduction_labels=reduction_labels, reduction_data=reduction_data)

# Page 2 : barres et camemberts
@app.route('/page2')
def page2():
    selected_first = request.args.get('first_category')
    selected_second = request.args.get('second_category')

    firsts = db.products.distinct('category_hierarchy.1')
    firsts = [f for f in firsts if f]
    firsts.sort()

    seconds = []
    if selected_first:
        seconds = db.products.distinct('category_hierarchy.2', {'category_hierarchy.1': selected_first})
        seconds = [s for s in seconds if s]
        seconds.sort()

    pipeline_bar = [
        {"$match": {"category_hierarchy.1": {"$ne": None}}},
        {"$group": {
            "_id": { "$arrayElemAt": ["$category_hierarchy", 1] },
            "count": { "$sum": 1 },
            "total_reviews": { "$sum": { "$toInt": "$review_count" } }
        }},
        {"$sort": { "_id": 1 }}
    ]
    category_counts = list(db.products.aggregate(pipeline_bar))
    labels_bar = [item['_id'] if item['_id'] else 'Non renseigné' for item in category_counts]
    data_bar = [item['count'] for item in category_counts]
    reviews_bar = [item['total_reviews'] for item in category_counts]

    pie_labels, pie_data, pie_reviews = [], [], []
    if selected_second:
        pipeline_pie = [
            {"$match": {"category_hierarchy.2": selected_second}},
            {"$group": {
                "_id": { "$arrayElemAt": ["$category_hierarchy", 3] },
                "count": { "$sum": 1 },
                "total_reviews": { "$sum": { "$toInt": "$review_count" } }
            }},
            {"$sort": { "count": -1 }}
        ]
        pie_counts = list(db.products.aggregate(pipeline_pie))
        pie_labels = [item['_id'] if item['_id'] else 'Non renseigné' for item in pie_counts]
        pie_data = [item['count'] for item in pie_counts]
        pie_reviews = [item.get('total_reviews', 0) for item in pie_counts]

    pie2_labels, pie2_data, pie2_reviews = [], [], []
    if selected_first:
        pipeline_pie2 = [
            {"$match": {"category_hierarchy.1": selected_first}},
            {"$group": {
                "_id": { "$arrayElemAt": ["$category_hierarchy", 2] },
                "count": { "$sum": 1 },
                "total_reviews": { "$sum": { "$toInt": "$review_count" } }
            }},
            {"$sort": { "count": -1 }}
        ]
        pie2_counts = list(db.products.aggregate(pipeline_pie2))
        pie2_labels = [item['_id'] if item['_id'] else 'Non renseigné' for item in pie2_counts]
        pie2_data = [item['count'] for item in pie2_counts]
        pie2_reviews = [item.get('total_reviews', 0) for item in pie2_counts]

    return render_template('page2.html', labels=labels_bar, data=data_bar,
                           reviews=reviews_bar,
                           firsts=firsts, selected_first=selected_first,
                           seconds=seconds, selected_second=selected_second,
                           pie_labels=pie_labels, pie_data=pie_data, pie_reviews=pie_reviews,
                           pie2_labels=pie2_labels, pie2_data=pie2_data, pie2_reviews=pie2_reviews)

# Page 3 : ranking moyen
@app.route('/page3')
def page3():
    # Premier graphique : ranking moyen par catégorie
    pipeline = [
        {"$match": {"category_hierarchy.1": {"$ne": None}, "rating": {"$ne": None, "$gt": 0}}},
        {"$addFields": {"rating_float": {"$toDouble": "$rating"}}},
        {"$group": {"_id": {"$arrayElemAt": ["$category_hierarchy", 1]}, "avg_rating": {"$avg": "$rating_float"}}},
        {"$sort": {"_id": 1}}
    ]
    results = list(collection.aggregate(pipeline))
    labels = [res['_id'] for res in results]
    data = [res['avg_rating'] for res in results]

    return render_template('page3.html', labels=labels, data=data)


def get_secondary_rating_types():
    try:
        query = {
            "size": 0,
            "aggs": {
                "ratings_nested": {
                    "nested": {"path": "secondaryRatings"},
                    "aggs": {
                        "labels": {
                            "terms": {"field": "secondaryRatings.label.keyword", "size": 100}
                        }
                    }
                }
            }
        }
        res = es.search(index="ikea_reviews", body=query)
        return [bucket['key'] for bucket in res['aggregations']['ratings_nested']['labels']['buckets']]
    except Exception as e:
        print(f"Erreur lors de la récupération des types de secondary ratings: {e}")
        return []


# Page 5 : moyenne par type de secondary rating (tous produits confondus)
@app.route('/page5')
def page5():
    query = {
        "size": 0,
        "aggs": {
            "ratings_nested": {
                "nested": {"path": "secondaryRatings"},
                "aggs": {
                    "labels": {
                        "terms": {"field": "secondaryRatings.label.keyword", "size": 100},
                        "aggs": {
                            "avg_rating": {"avg": {"field": "secondaryRatings.ratingValue"}}
                        }
                    }
                }
            }
        }
    }

    labels = []
    data = []
    error_msg = None
    try:
        res = es.search(index="ikea_reviews", body=query)
        buckets = res['aggregations']['ratings_nested']['labels']['buckets']
        print("Buckets bruts pour page5:", buckets)
        if not buckets:
            error_msg = "Aucune donnée trouvée pour les secondaryRatings. Vérifiez l'indexation."
        for bucket in buckets:
            avg_val = bucket['avg_rating'].get('value')
            if avg_val is not None:
                labels.append(bucket['key'])
                data.append(avg_val)
    except Exception as e:
        error_msg = f"Erreur Elasticsearch pour page5: {e}"

    return render_template('page5.html', labels=labels, data=data, error_msg=error_msg)

#page4
@app.route('/search_es', methods=['GET', 'POST'])
def search_es():
    results = []
    query_word = ''
    if request.method == 'POST':
        query_word = request.form.get('query_word', '').strip()
        if query_word:
            es_query = {
                "size": 20,
                "query": {
                    "nested": {
                        "path": "reviews",
                        "query": {
                            "multi_match": {
                                "query": query_word,
                                "fields": ["reviews.comment", "reviews.text"]
                            }
                        }
                    }
                }
            }
            try:
                es_res = es.search(index="ikea_reviews", body=es_query)
                for hit in es_res['hits']['hits']:
                    doc = hit['_source']
                    for review in doc.get('reviews', []):
                        comment = review.get('comment', '') or review.get('text', '')
                        if query_word.lower() in comment.lower():
                            results.append({
                                'product': doc.get('name', 'Inconnu'),
                                'category': doc.get('category_main', 'Inconnu'),
                                'comment': comment
                            })
            except Exception as e:
                print(f"Erreur Elasticsearch: {e}")
    return render_template('search_es.html', results=results, query_word=query_word)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)