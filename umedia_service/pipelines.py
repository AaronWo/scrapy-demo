# -*- coding: utf-8 -*-
import codecs
import json
import time

from scrapy import signals
from scrapy.contrib.exporter import JsonItemExporter


# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
class UmediaServicePipeline(object):
    

    def __init__(self, **kwargs):
        self.files = {}
    
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline
    
    def spider_closed(self, spider):
        myfile = self.files.pop(spider)
        myfile.write(']')
        myfile.close()

    
    def spider_opened(self, spider):
        myfile = codecs.open(str(int(time.time())) + '.json', 'w+b', encoding='utf-8')
        self.files[spider] = myfile
        myfile.write('[')
    
    def process_item(self, item, spider):
        mData = dict()
        mData['ItemId'] = item['ItemId']
        mData['Url'] = item['Url']
        mData['Title'] = item['Title']
        mData['Category'] = item['Category']
        jsonstr = json.dumps(mData)
        self.files[spider].write(jsonstr + ',')
        return item
