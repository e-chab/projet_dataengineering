from flask import Flask, render_template, request
from pymongo import MongoClient

app = Flask(__name__)

# Configuration MongoDB
MONGO_URI = 'mongodb://mongodb:27017/'
client = MongoClient(MONGO_URI)
db = client['ikea_db']
collection = db['products']


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

    base_messages = ['Nouveau', 'Prix le plus bas']
    combined_message = 'Prix le plus bas & Nouveau'
    message_types = [base_messages[0], combined_message, base_messages[1]]

    data_counts = [[], [], []]
    for cat in categories:
        count_nouveau = db.products.count_documents({"category_hierarchy.1": cat, "commercial_message": 'Nouveau'})
        count_prix_le_plus_bas = db.products.count_documents({"category_hierarchy.1": cat, "commercial_message": 'Prix le plus bas'})
        count_combined = db.products.count_documents({"category_hierarchy.1": cat, "commercial_message": combined_message})
        data_counts[0].append(count_nouveau)
        data_counts[1].append(count_combined)
        data_counts[2].append(count_prix_le_plus_bas)

    return render_template('index.html', categories=categories, message_types=message_types, data_counts=data_counts)

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
    pipeline = [
        {
            "$match": {
                "category_hierarchy.1": {"$ne": None},
                "rating": {"$ne": None, "$ne": ""}
            }
        },
        {
            "$addFields": {
                "rating_float": {"$toDouble": "$rating"}
            }
        },
        {
            "$group": {
                "_id": {"$arrayElemAt": ["$category_hierarchy", 1]},
                "avg_rating": {"$avg": "$rating_float"},
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    rating_data = list(collection.aggregate(pipeline))
    labels = [item['_id'] for item in rating_data]
    data = [round(item['avg_rating'] if item['avg_rating'] is not None else 0, 2) for item in rating_data]
    return render_template('page3.html', labels=labels, data=data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)