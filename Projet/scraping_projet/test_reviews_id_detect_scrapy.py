import scrapy
import re

class ProductIdDetectSpider(scrapy.Spider):
    name = "product_id_detect"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = [
        "https://www.ikea.com/fr/fr/p/vattenkrasse-arrosoir-ivoire-couleur-or-40394118/"
    ]

    def parse(self, response):
        # Méthode 1 : Extraire l'ID depuis l'URL
        product_id_url = re.search(r"-(\d+)/?$", response.url)
        product_id = product_id_url.group(1) if product_id_url else None
        self.logger.info(f"Product ID extrait de l'URL: {product_id}")
        self.logger.info(f"URL du produit: {response.url}")

        # Méthode 2 : Chercher l'ID dans le HTML (meta)
        meta_id = response.css('meta[property="product:item_number"]::attr(content)').get()
        if meta_id:
            self.logger.info(f"Product ID extrait du HTML (meta): {meta_id}")
        else:
            self.logger.info("Aucun product ID trouvé dans le HTML (meta)")

        # Test de la requête reviews si un ID a été trouvé
        if product_id:
            yield scrapy.Request(
                url=f"https://web-api.ikea.com/tugc/public/v5/reviews/fr/fr/{product_id}",
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/plain, */*",
                    "x-client-id": "a1047798-0fc4-446e-9616-0afe3256d0d7",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
                },
                body='{"filter": {"and": [], "not": []}, "sort": [{"field": "submissionOn", "direction": "desc"}], "page": {"size": 20, "number": 1}}',
                callback=self.parse_reviews,
                meta={"product_id": product_id}
            )
        else:
            self.logger.info("Impossible de trouver un product_id pour la page.")

    def parse_reviews(self, response):
        product_id = response.meta.get("product_id")
        self.logger.info(f"Réponse reviews pour product_id: {product_id}, status: {response.status}")
        try:
            reviews = response.json()
            self.logger.info(f"Nombre d'avis trouvés: {len(reviews)}")
            for review in reviews:
                self.logger.info(f"Auteur: {review.get('reviewer', {}).get('displayName')}")
                self.logger.info(f"Titre: {review.get('title')}")
                self.logger.info(f"Texte: {review.get('text')}")
                self.logger.info(f"Note: {review.get('primaryRating', {}).get('ratingValue')}")
                self.logger.info("-")
        except Exception as e:
            self.logger.error(f"Erreur lors du décodage JSON: {e}")
