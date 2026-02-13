# Projet Data Engineering

Ce projet est une solution complète de data engineering comprenant un module de scraping, une API web, et une orchestration via Docker Compose. Il permet de collecter, traiter et visualiser des données scrapées à partir du site IKEA France.

## Technologies utilisées et justification

- **Python** : Langage principal pour le développement du scraping et de l’application web, reconnu pour sa simplicité, sa richesse en bibliothèques et sa communauté active.
- **Scrapy** : Framework Python spécialisé dans le scraping web. Il permet d’extraire efficacement des données structurées à grande échelle, de gérer les requêtes asynchrones et de manipuler facilement les pipelines de données.
- **Flask** : Micro-framework web Python utilisé pour créer l’API et le dashboard. Il est léger, flexible et adapté à la création rapide d’applications web et d’APIs REST. Flask utilise le moteur de templates **Jinja2** pour générer dynamiquement les pages HTML à partir des données (Jinja2 est donc utilisé indirectement).
- **MongoDB** : Base de données NoSQL utilisée pour stocker les produits et avis collectés. Elle permet une grande flexibilité dans la structure des données et des requêtes d’agrégation puissantes.
- **Elasticsearch** : Moteur de recherche et d’indexation utilisé pour effectuer des recherches textuelles avancées et des agrégations rapides sur les avis et produits collectés.
- **Docker & Docker Compose** : Outils de conteneurisation et d’orchestration. Ils assurent la portabilité, l’isolation et la reproductibilité de l’environnement de développement et de production. Docker Compose facilite le lancement simultané de plusieurs services (scraping, web, base de données, etc.).

Ces choix technologiques garantissent une architecture modulaire, maintenable, évolutive et adaptée à la manipulation et l’analyse de données à grande échelle.

## Fonctionnement du projet et architecture

Le projet s’articule autour de trois grands modules : le scraping (collecte de données), le stockage et l’indexation, et l’application web de visualisation/recherche.

### 1. Scraping des données IKEA

- Le scraping commence à partir de la page listant toutes les catégories de produits IKEA France.
- Le spider Scrapy parcourt récursivement toutes les sous-catégories pour trouver l’ensemble des produits disponibles.
- Sur chaque page produit, plusieurs informations sont extraites :
   - Les messages commerciaux : ils peuvent apparaître sous forme de carré texte près de l’image, d’un prix barré avec un prix réduit, ou d’un texte à côté du nom du produit.
   - Les autres informations produit (nom, catégorie, etc.).
   - Les commentaires/avis clients : ceux-ci ne sont pas présents directement dans le HTML, mais sont chargés dynamiquement via une API. Le spider interroge cette API pour chaque produit et récupère les avis au format JSON.

### 2. Stockage et indexation des données

- Les données extraites sont envoyées en temps réel vers MongoDB (base NoSQL) grâce à un pipeline Scrapy dédié.
- En parallèle, un pipeline Scrapy indexe également les données dans Elasticsearch pour permettre des recherches et agrégations rapides.
(Généralement, l’indexation d’Elasticsearch se fait à partir de MongoDB via un connecteur ou un ETL, mais ici les données sont envoyées directement depuis Scrapy, ce qui permet une indexation immédiate sans étape intermédiaire, j'ai fait ce choix car cela semblait plus simple qu'un remplissage au fur et à mesure de Elasticsearch via MongoDB.)
- Ces opérations de stockage et d’indexation peuvent se faire pendant que l’application web est en fonctionnement.

### 3. Application web et visualisation

- L’application web (Flask) peut tourner en même temps que le scraping.
- Elle interroge MongoDB pour afficher des statistiques, des listes de produits, des analyses de messages commerciaux, etc.
- Elle interroge Elasticsearch pour effectuer des recherches textuelles avancées et des agrégations sur les avis et produits.

### 4. Orchestration et concurrence

- Grâce à Docker Compose, les services de scraping, MongoDB, Elasticsearch et l’application web peuvent tourner simultanément et indépendamment.
- Le scraping peut donc alimenter MongoDB et Elasticsearch en continu, pendant que l’application web exploite les données déjà présentes ou nouvellement ajoutées.

Cette architecture permet une collecte, un enrichissement et une exploitation des données en temps réel, tout en assurant la modularité et la robustesse du système.

## Structure du projet

```
Projet/
├── docker-compose.yml           # Orchestration des services avec Docker
├── test_categories.py           # Script de test des catégories
├── start_dashboard.bat          # Script batch de lancement rapide
├── scraping_projet/             # Module de scraping (Scrapy)
│   ├── Dockerfile               # Image Docker pour le scraping
│   ├── requirements.txt         # Dépendances Python pour le scraping
│   ├── scrapy.cfg               # Configuration Scrapy
│   └── scraping_projet/         # Code source Scrapy
│       ├── __init__.py
│       ├── items.py             # Définition des items Scrapy
│       ├── middlewares.py       # Middlewares Scrapy
│       ├── pipelines.py         # Pipelines de traitement
│       ├── settings.py          # Paramètres Scrapy
│       └── spiders/             # Spiders Scrapy
│           └── ikea_retriever.py# Spider IKEA principal
├── web_projet/                  # Application web (Flask)
│   ├── app.py                   # Application principale Flask
│   ├── Dockerfile               # Image Docker pour l'app web
│   ├── requirements.txt         # Dépendances Python pour l'app web
│   ├── static/                  # Images statiques (captures d'écran, etc.)
│   │   ├── page1.PNG
│   │   ├── page2.PNG
│   │   ├── page3.PNG
│   │   ├── page4.PNG
│   │   └── page5.PNG
│   └── templates/               # Templates HTML (Jinja2)
│       ├── page0.html           # Présentation
│       ├── page1.html           # Messages commerciaux
│       ├── page2.html           # Nombre de commentaires
│       ├── page3.html           # Notes des commentaires
│       ├── page4.html           # Gamme de produit
│       └── page5.html           # Commentaires
```


## Prérequis

- Docker Desktop pour [Docker](https://www.docker.com/) et [Docker Compose](https://docs.docker.com/compose/)
- Python 3.8+ (uniquement si vous souhaitez lancer les scripts en dehors de Docker)

> Toutes les autres dépendances (Python, Scrapy, Flask, MongoDB, Elasticsearch, etc.) sont automatiquement installées dans les conteneurs Docker respectifs lors du build. Aucune installation manuelle supplémentaire n'est requise sur votre machine.


## Installation & Lancement

1. **Cloner le dépôt**
   ```bash
   git clone <url-du-repo>
   cd Projet
   ```
2. **Lancer les services avec Docker Compose**
   ```bash
   docker-compose up --build
   ```
3. **Accéder à l'application web**
   - Ouvrir un navigateur à l'adresse : http://localhost:5000

## Auteurs

Elise Chabrerie
