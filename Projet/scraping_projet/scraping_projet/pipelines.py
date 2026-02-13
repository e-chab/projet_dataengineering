import pymongo
from scrapy.exceptions import DropItem
from elasticsearch import Elasticsearch, helpers
import os
import time

class ElasticsearchPipeline:
    def __init__(self, es_hosts):
        self.es = Elasticsearch(es_hosts)
        self.index_name = 'ikea_reviews'

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            es_hosts=crawler.settings.get('ELASTICSEARCH_HOSTS')
        )

    def open_spider(self, spider):
        # Supprime l'index s'il existe pour garantir le mapping
        if self.es.indices.exists(index=self.index_name):
            self.es.indices.delete(index=self.index_name)
        self.es.indices.create(index=self.index_name, body={
            "mappings": {
                "properties": {
                    "category_hierarchy": {"type": "keyword"},
                    "category_main": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "description": {"type": "text"},
                    "image_url": {"type": "keyword"},
                    "price": {"type": "float"},
                    "product_id": {"type": "keyword"},
                    "commercial_message": {"type": "keyword"},
                    "rating": {"type": "float"},
                    "review_count": {"type": "integer"},
                    "reviews": {
                        "type": "nested",
                        "properties": {
                            "id": {"type": "keyword"},
                            "text": {"type": "text"},
                            "comment": {"type": "text"},
                            "title": {"type": "text"},
                            "sourceCountryCode": {"type": "keyword"},
                            "sourceLangCode": {"type": "keyword"},
                            "submissionOn": {"type": "date"},
                            "updatedOn": {"type": "date"},
                            "isRecommended": {"type": "boolean"},
                            "primaryRating": {
                                "properties": {
                                    "ratingRange": {"type": "integer"},
                                    "ratingValue": {"type": "float"}
                                }
                            },
                            "secondaryRatings": {
                                "type": "nested",
                                "properties": {
                                    "id": {"type": "keyword"},
                                    "label": {"type": "keyword"},
                                    "ratingRange": {"type": "integer"},
                                    "ratingValue": {"type": "float"}
                                }
                            }
                        }
                    },
                    "secondaryRatings": {
                        "type": "nested",
                        "properties": {
                            "label": {"type": "keyword"},
                            "ratingValue": {"type": "float"}
                        }
                    }
                }
            }
        })

    def process_item(self, item, spider):
        actions = []
        category_hierarchy = item.get('category_hierarchy', [])
        category_main = category_hierarchy[1] if len(category_hierarchy) > 1 else None
        reviews = item.get('reviews', [])
        # On stocke toutes les reviews dans un seul document
        source = {
            "category_hierarchy": category_hierarchy,
            "category_main": category_main,
            "name": item.get('name'),
            "description": item.get('description'),
            "image_url": item.get('image_url'),
            "price": item.get('price'),
            "product_id": item.get('product_id'),
            "commercial_message": item.get('commercial_message'),
            "rating": item.get('rating'),
            "review_count": item.get('review_count'),
            "reviews": reviews
        }
        # On collecte tous les secondaryRatings au niveau top-level pour l'agrégation
        secondary_ratings = []
        for review in reviews:
            if review and review.get('secondaryRatings'):
                secondary_ratings.extend(review['secondaryRatings'])
        if secondary_ratings:
            source["secondaryRatings"] = secondary_ratings
        action = {
            "_index": self.index_name,
            "_source": source
        }
        actions.append(action)
        if actions:
            try:
                helpers.bulk(self.es, actions)
            except Exception as e:
                spider.logger.error(f"Erreur lors de l'indexation sur Elasticsearch: {e}")
        return item

class MongoDBPipeline:
    def __init__(self, mongo_uri, mongo_db, collection_name):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.collection_name = collection_name

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items'),
            collection_name=crawler.settings.get('MONGO_COLLECTION', 'ikea_products')
        )

    def open_spider(self, spider):
        try:
            self.client = pymongo.MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.client.server_info()
            self.db = self.client[self.mongo_db]
            self.collection = self.db[self.collection_name]
            spider.logger.info(f"[MongoDBPipeline] Connexion réussie à {self.mongo_uri}")
        except Exception as e:
            spider.logger.error(f"[MongoDBPipeline] Erreur de connexion à MongoDB: {e}")
            self.client = None
            self.collection = None

    def close_spider(self, spider):
        if self.client:
            self.client.close()

    def process_item(self, item, spider):
        if self.collection is not None:
            try:
                self.collection.insert_one(dict(item))
                spider.logger.debug(f"Item inséré dans MongoDB: {item.get('url')}")
            except Exception as e:
                spider.logger.error(f"Erreur lors de l'insertion MongoDB: {e}")
        return item

class DuplicatesPipeline:
    def __init__(self):
        self.urls_seen = set()

    def process_item(self, item, spider):
        if 'url' in item and item['url'] in self.urls_seen:
            raise DropItem(f"Duplicate item found: {item['url']}")
        else:
            self.urls_seen.add(item['url'])
            return item

