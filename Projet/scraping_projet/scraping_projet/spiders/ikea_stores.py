
import scrapy

class IkeaStoresSpider(scrapy.Spider):
    name = 'ikea_stores'
    allowed_domains = ['ikea.com']
    start_urls = ['https://www.ikea.com/fr/fr/']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {'headless': True},
    }

    def start_requests(self):
        yield scrapy.Request(
            self.start_urls[0],
            meta={
                'playwright': True,
                'playwright_page_methods': [
                    {"method": "wait_for_selector", "args": ['a[href*="store"]']}
                ],
            },
            callback=self.parse
        )

    def parse(self, response):
        # Extraction des adresses des magasins IKEA
        stores = []
        for store in response.css('div[data-component="StoreCard"]'):
            name = store.css('h2::text').get()
            address = store.css('address::text').get()
            if name and address:
                stores.append({'name': name.strip(), 'address': address.strip()})

        # Sauvegarde dans un fichier JSON
        import json
        with open('/output/stores.json', 'w', encoding='utf-8') as f:
            json.dump(stores, f, ensure_ascii=False, indent=2)
        self.log(f"{len(stores)} magasins IKEA extraits et sauvegardés dans stores.json")