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

# Page 2 : Nombre de reviews 
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
        res = es.search(index="ikea_reviews", **query)
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

    return render_template('page4_non.html', labels=labels, data=data, error_msg=error_msg)

#page4
@app.route('/page5', methods=['GET', 'POST'])
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
                es_res = es.search(index="ikea_reviews", **es_query)
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
    return render_template('page5.html', results=results, query_word=query_word)


# Page 6: Recherche de produit par nom et répartition des ratings
@app.route('/page4')
def page4():
    product_name = request.args.get('product_name', '').strip()
    
    rating_labels = []
    rating_data = []
    total_reviews = 0
    product_count = 0
    error_message = None
    secondary_ratings_data = {}
    
    if product_name:
        try:
            # Recherche des produits par nom dans Elasticsearch
            query = {
                "size": 1000,  # Récupérer tous les produits correspondants
                "query": {
                    "match": {
                        "name": {
                            "query": product_name,
                            "operator": "and"
                        }
                    }
                }
            }
            
            res = es.search(index="ikea_reviews", **query)
            hits = res.get('hits', {}).get('hits', [])
            
            if hits:
                product_count = len(hits)
                rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                secondary_ratings_counts = {}
                
                # Parcourir tous les produits trouvés
                for hit in hits:
                    source = hit.get('_source', {})
                    reviews = source.get('reviews', [])
                    
                    # Compter les ratings de chaque review
                    for review in reviews:
                        if review and review.get('primaryRating'):
                            rating_value = review['primaryRating'].get('ratingValue')
                            if rating_value:
                                # Arrondir le rating à l'entier le plus proche
                                rounded_rating = round(rating_value)
                                if 1 <= rounded_rating <= 5:
                                    rating_counts[rounded_rating] += 1
                                    total_reviews += 1
                        
                        # Compter les secondaryRatings
                        if review and review.get('secondaryRatings'):
                            for sec_rating in review['secondaryRatings']:
                                label = sec_rating.get('label')
                                rating_value = sec_rating.get('ratingValue')
                                if label and rating_value:
                                    if label not in secondary_ratings_counts:
                                        secondary_ratings_counts[label] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                                    rounded_rating = round(rating_value)
                                    if 1 <= rounded_rating <= 5:
                                        secondary_ratings_counts[label][rounded_rating] += 1
                
                if total_reviews > 0:
                    # Préparer les données pour le graphique primary
                    rating_labels = ['1 étoile', '2 étoiles', '3 étoiles', '4 étoiles', '5 étoiles']
                    rating_data = [rating_counts[1], rating_counts[2], rating_counts[3], 
                                   rating_counts[4], rating_counts[5]]
                    
                    # Préparer les données pour les graphiques secondaryRatings
                    for label, counts in secondary_ratings_counts.items():
                        secondary_ratings_data[label] = {
                            'labels': rating_labels,
                            'data': [counts[1], counts[2], counts[3], counts[4], counts[5]],
                            'total': sum(counts.values())
                        }
                else:
                    error_message = f"Aucune review trouvée pour le produit '{product_name}'."
            else:
                error_message = f"Aucun produit trouvé avec le nom '{product_name}'."
        
        except Exception as e:
            error_message = f"Erreur lors de la recherche: {str(e)}"
            print(f"Erreur Elasticsearch: {e}")
    
    return render_template('page4.html', 
                          product_name=product_name,
                          rating_labels=rating_labels,
                          rating_data=rating_data,
                          total_reviews=total_reviews,
                          product_count=product_count,
                          error_message=error_message,
                          secondary_ratings_data=secondary_ratings_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)