import os

LOG_LEVEL = 'DEBUG'

BOT_NAME = "scraping_projet"

SPIDER_MODULES = ["scraping_projet.spiders"]
NEWSPIDER_MODULE = "scraping_projet.spiders"

ROBOTSTXT_OBEY = True

ITEM_PIPELINES = {
   "scraping_projet.pipelines.DuplicatesPipeline": 300,
   "scraping_projet.pipelines.MongoDBPipeline": 400,
   "scraping_projet.pipelines.ElasticsearchPipeline": 500,
}

# MongoDB settings
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://mongodb:27017/')
MONGO_DATABASE = 'ikea_db'
MONGO_COLLECTION = 'products'

# Elasticsearch settings
ELASTICSEARCH_HOSTS = os.environ.get('ELASTICSEARCH_HOSTS', 'http://localhost:9200')

