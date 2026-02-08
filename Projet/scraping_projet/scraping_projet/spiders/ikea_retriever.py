import scrapy
from scrapy.http import Request
from ..items import IkeaProductItem
import json
import re

class IkeaSpider(scrapy.Spider):
    # Compteurs pour chaque type de message
    message_counts = {
        'cat_principale': 0,
        'cat': 0,
        'sous_cat': 0,
        'produits': 0,
        'produit': 0,
        'produits_next': 0
    }
    name = "ikea"
    allowed_domains = ["ikea.com"]
    start_urls = ["https://www.ikea.com/fr/fr/cat/produits-products/"]

    def parse(self, response, **kwargs):
        """
        Cette méthode parse la page principale des produits pour trouver les catégories.
        """
        print(f"[SCRAP] Page principale des catégories : {response.url}")
        self.message_counts['cat_principale'] += 1
        
        # Cible les liens des catégories principales
        category_links = response.css('a.vn-link.vn-nav__link')
        print(f"[SCRAP] -> Nombre de catégories principales trouvées : {len(category_links)}")

        for link in category_links:
            category_url = link.attrib['href']
            category_name = link.css('span::text').get()
            
            if category_url and category_name:
                print(f"[SCRAP] -> Catégorie trouvée : {category_name.strip()} ({response.urljoin(category_url)})")
                self.message_counts['cat'] += 1
                # Pour chaque catégorie, on lance le parsing des sous-catégories
                yield Request(
                    url=response.urljoin(category_url),
                    callback=self.parse_sub_categories,
                    meta={'category_path': [category_name.strip()]}
                )

    def parse_sub_categories(self, response):
        print(f"[SCRAP] Page sous-catégorie : {response.url}")
        self.message_counts['sous_cat'] += 1
        # Récupère le chemin de la catégorie actuelle.
        category_path = response.meta['category_path']
        
        # Cherche le conteneur du carrousel de navigation. Attention il y a des carrousel même sur des pages de produits pour voir les articles similaires.
        sub_category_carousel = response.css('div.plp-navigation-slot-wrapper div.hnf-carousel__wrapper div.hnf-carousel-slide')[1:]

        print(f"[SCRAP] -> Nombre de sous-catégories trouvées : {len(sub_category_carousel)}")
        found_subcat = False
        for slide in sub_category_carousel:
            for link in slide.css('a[href]'):
                sub_cat_url = link.attrib['href']
                sub_cat_name = link.css('span::text').get() or link.css('::text').get() or sub_cat_url
                if sub_cat_url:
                    found_subcat = True
                    print(f"[SCRAP] -> Considéré comme sous-catégorie : {sub_cat_name.strip()} ({response.urljoin(sub_cat_url)})")
                    self.message_counts['sous_cat'] += 1
                    new_category_path = category_path + [sub_cat_name.strip()]
                    yield Request(
                        url=response.urljoin(sub_cat_url),
                        callback=self.parse_sub_categories,
                        meta={'category_path': new_category_path}
                    )
        if not found_subcat:
            print(f"[SCRAP] -> Aucune sous-catégorie trouvée, on parse les produits : {response.url}")
            yield from self.parse_products(response)

    def parse_products(self, response):
        """
        Parse la page de liste de produits, extrait l'URL de chaque produit et
        délègue le scraping à parse_product_details.
        """
        # Cible les liens vers les pages de produits.
        product_links = response.css('#product-list div.plp-mastercard a.plp-price-link-wrapper::attr(href)').getall()
        
        if not product_links:
            self.logger.warning("Aucun lien de produit trouvé sur %s", response.url)
            return

        self.logger.info(f"Trouvé {len(product_links)} liens de produits sur la page {response.url}")

        for link in product_links:
            # Pour chaque lien, on suit vers la page de détails du produit.
            yield response.follow(link, self.parse_product_details, meta=response.meta)

    def parse_product_details(self, response):
        """
        Cette fonction parse la page d'un produit pour en extraire les détails.
        Elle utilise des sélecteurs CSS robustes pour gérer différentes mises en page.
        """
        print(f"[SCRAP] Page produit : {response.url}")
        self.message_counts['produit'] += 1
        
        item = IkeaProductItem()

        # Message commercial (ex: "Nouveau", "Prix le plus bas")
        commercial_message_element = response.css('div.pipf-price-package div.pipcom-commercial-message') #.pipf-price-package permet de cibler le commentaire du produit principale et non d'autres mentionnés
        commercial_message = ''
        if commercial_message_element:
            # Récupère tout le texte contenu dans la balise, y compris les sous-éléments
            commercial_message_parts = commercial_message_element.css('::text').getall()
            commercial_message = ' '.join(part.strip() for part in commercial_message_parts if part.strip()).strip()

        # Vérifie si le prix est mis en valeur (balise <em>) pour ajouter "Prix le plus bas"
        if response.css('div.pipf-price-package em.pipcom-price'):  #.pipf-price-package permet de cibler le prix du produit principale et non d'autres mentionnés
            if commercial_message and "Prix le plus bas" not in commercial_message:
                commercial_message = 'Prix le plus bas ' + commercial_message
            elif "Prix le plus bas" not in commercial_message:
                commercial_message = 'Prix le plus bas'
        
        item['commercial_message'] = commercial_message

        # Hiérarchie des catégories depuis le fil d'Ariane
        breadcrumb_links = response.css('ol.hnf-breadcrumb__list li.hnf-breadcrumb__list-item a span::text').getall()
        categories = [cat.strip() for cat in breadcrumb_links if cat.strip()]
        item['category_hierarchy'] = categories

        # Nom du produit
        item['name'] = response.css('h1 .pipcom-price-module__name-decorator::text').get(default='').strip()

        # Description
        description_parts = response.css('h1 .pipcom-price-module__description *::text').getall()
        item['description'] = ' '.join(part.strip() for part in description_parts if part.strip())

        # Prix
        price_text = response.css('.pipcom-price__sr-text::text').get()
        if price_text:
            price_match = re.search(r'(\d+,\d+)', price_text)
            if price_match:
                item['price'] = float(price_match.group(1).replace(',', '.'))
            else:
                item['price'] = 0.0
        else:
            item['price'] = 0.0

        # URL de l'image principale
        item['image_url'] = response.css('div.pip-media-grid__media-container img::attr(src)').get()

        # Évaluation (Rating)
        rating_text = response.css('.pipf-rating .pipf-rating__stars::attr(aria-label)').get()
        if rating_text:
            # Extrait la note de "Avis: 4.4 sur 5 étoiles..."
            rating_match = re.search(r'Avis:\s*([\d,\.]+)', rating_text)
            if rating_match:
                item['rating'] = float(rating_match.group(1).replace(',', '.'))
            else:
                item['rating'] = 0.0
        else:
            item['rating'] = 0.0
            
        # Nombre d'avis (Review Count)
        review_count_text = response.css('.pipf-rating__label::text').get()
        if review_count_text:
            try:
                item['review_count'] = int(review_count_text.strip('()'))
            except (ValueError, TypeError):
                item['review_count'] = 0
        else:
            # Si le sélecteur principal échoue, on essaie de l'extraire de l'aria-label
            if rating_text:
                review_match = re.search(r'Nombre total d\'avis:\s*(\d+)', rating_text)
                if review_match:
                    item['review_count'] = int(review_match.group(1))
                else:
                    item['review_count'] = 0
            else:
                item['review_count'] = 0

        # URL de la page
        item['url'] = response.url

        yield item

    def close(self, reason):
        print("\nRésumé des messages printés :")
        print(f"Catégories principales : {self.message_counts['cat_principale']}")
        print(f"Catégories : {self.message_counts['cat']}")
        print(f"Sous-catégories : {self.message_counts['sous_cat']}")
        print(f"Pages de produits : {self.message_counts['produits']}")
        print(f"Produits : {self.message_counts['produit']}")
        print(f"Pages suivantes de produits : {self.message_counts['produits_next']}")