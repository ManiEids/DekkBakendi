# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TireItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    manufacturer = scrapy.Field()
    price = scrapy.Field()
    tire_size = scrapy.Field()
    width = scrapy.Field()
    aspect_ratio = scrapy.Field()
    rim_size = scrapy.Field()
    stock = scrapy.Field()
    inventory = scrapy.Field()
    picture = scrapy.Field()
    seller = scrapy.Field()
