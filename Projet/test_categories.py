import scrapy
from scrapy.crawler import CrawlerProcess

class CategoryTestSpider(scrapy.Spider):
    name = "category_tester"
    start_urls = [
        'https://www.ikea.com/fr/fr/cat/cuisine-et-electromenager-ka001/'
    ]

    def parse(self, response, level=0):
        indent = "  " * level
        self.log(f"{indent}--- Analyse de la page : {response.url} ---")
        
        # Cible les cartes de catégories dans le carrousel de navigation
        sub_category_links = response.css('a.hnf-inpage-nav__card')

        if not sub_category_links:
            self.log(f"{indent}Aucune autre sous-catégorie trouvée. Fin de cette branche.")
            return

        self.log(f"{indent}{len(sub_category_links)} sous-catégories trouvées :")
        for link in sub_category_links:
            name = link.css('span.hnf-inpage-nav__label::text').get()
            url = link.attrib['href']
            
            if name and url:
                full_url = response.urljoin(url)
                print(f"{indent}- Trouvé: {name.strip()} -> {full_url}")
                # Pour chaque sous-catégorie, on lance une nouvelle requête
                yield scrapy.Request(
                    url=full_url, 
                    callback=self.parse,
                    cb_kwargs={'level': level + 1} # On passe le niveau pour l'indentation
                )

# --- Pour exécuter ce script directement ---
if __name__ == "__main__":
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
        'LOG_LEVEL': 'INFO', # Affiche moins de logs pour une sortie plus propre
    })

    process.crawl(CategoryTestSpider)
    process.start()
