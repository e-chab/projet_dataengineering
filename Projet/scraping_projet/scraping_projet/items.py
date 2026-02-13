import scrapy

class IkeaProductItem(scrapy.Item):
    product_id = scrapy.Field()
    name = scrapy.Field()
    price = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()
    image_url = scrapy.Field()
    category = scrapy.Field()
    sub_category = scrapy.Field()
    category_hierarchy = scrapy.Field()
    rating = scrapy.Field()
    review_count = scrapy.Field()
    is_new = scrapy.Field()
    commercial_message = scrapy.Field()
    reviews = scrapy.Field()
    sourceCountryCode = scrapy.Field()
