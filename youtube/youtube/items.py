# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class YoutubeItem(scrapy.Item):
    # define the fields for your item here like:
    videoId = scrapy.Field()
    title = scrapy.Field()
    lengthText = scrapy.Field()
    pass
