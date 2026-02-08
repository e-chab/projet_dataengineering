# Utiliser une image Python

FROM python:3.9-slim



# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers du projet
COPY . .

RUN pip install --no-cache-dir scrapy pymongo

# La commande pour lancer le spider ikea_retriever
CMD ["scrapy", "crawl", "ikea"]
