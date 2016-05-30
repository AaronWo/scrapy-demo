# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class UmediaServiceItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class Kr36Item(scrapy.Item):
    ItemId = scrapy.Field()
    Title = scrapy.Field()
    Url = scrapy.Field()
    Category = scrapy.Field()
