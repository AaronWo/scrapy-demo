# encoding:utf-8
'''
Created on 2014年8月4日

@author: haosuwo@gmail.com 呙昊甦
'''
import codecs
import hashlib
import json
import re
import time
import urllib2
import urlparse

from BeautifulSoup import BeautifulSoup
from scrapy import log, signals
import scrapy
from scrapy.contrib.spiders.crawl import CrawlSpider

class OnceSpider(CrawlSpider):
    """this spider just get the start_urls from the HBase, crawl the start urls,
    analysis the results and then insert them into the HBase and never request again"""
    start_urls = [\
                  'http://www.36kr.com/topic/startups',
                  'http://www.36kr.com/topic/products',
                  'http://www.36kr.com/topic/apps',
                  'http://www.36kr.com/topic/technology',
                  'http://www.36kr.com/topic/websites',
                  'http://www.36kr.com/topic/people',
                  'http://www.36kr.com/topic/brands',
                  'http://www.36kr.com/topic/devices'
                  ]
#     start_urls = ['http://www.36kr.com/topic/technology']
    name = "umedia_spider"
    allowed_domains = ['36kr.com']

    
    def __init__(self, *a, **kwargs):
        super(OnceSpider, self).__init__(*a, **kwargs)
        self.data = []
        self.items = []
        
        
    def start_requests(self):
        for url in self.start_urls:
            mMeta = dict()
            if url.__contains__('startups'):
                mMeta['category'] = u'\u521B\u4E1A\u516C\u53F8'
            elif url.__contains__('products'):
                mMeta['category'] = u'\u4EA7\u54C1'
            elif url.__contains__('apps'):
                mMeta['category'] = u'\u5E94\u7528\u8F6F\u4EF6'
            elif url.__contains__('technology'):
                mMeta['category'] = '科技'
            elif url.__contains__('websites'):
                mMeta['category'] = u'\u7F51\u7AD9'
            elif url.__contains__('people'):
                mMeta['category'] = u'\u7F51\u7AD9'
            elif url.__contains__('brands'):
                mMeta['category'] = u'\u7F51\u7AD9'
            elif url.__contains__('devices'):
                mMeta['category'] = u'\u7F51\u7AD9'
            yield scrapy.Request(url, meta=mMeta, dont_filter=False, callback=self.parse)


    def process_raw_content(self, response):
        """ at first, we should determine whether this page should be analysed . and then, we process the content of the page, 
        including the data structure and the content link. Then, we insert the structured content into the ES
        @param response: the Response object of the SCRAPY """
        self.log('processing raw content')
        result = re.search(r'www.36kr.com/p/(\d*).htm', response.url, re.I)
        if result:
            self.log('News Page!')
            soup = BeautifulSoup(response.body)
            mdata = dict()
            myMD5 = hashlib.md5()
            myMD5.update(response.url)
            mdata['ItemId'] = myMD5.hexdigest()
            mdata['DisplaySwitch'] = 'on'
            mdata['Url'] = response.url
            
            Properties = dict()
            Properties['Quality'] = 0.5            
            Properties['Category'] = ['Internet', '36kr', response.meta['category']]
            Properties['CreateTime'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            mdata['Properties'] = Properties
            try:
                title = soup.find('h1', attrs={'class':'single-post__title'}).text
                Indexed = dict()
                Indexed['Title'] = title
#                 print title
            except Exception, e:
                print e
            try:
                content_wrapper = soup.find('div', attrs={'class':'content-wrapper'})
                mdata['Auxiliary'] = content_wrapper.find('img')['src']
                tag_ps = content_wrapper.findAll('p')
                content = ''
                for tag_p in tag_ps:
                    content += tag_p.text + '#$#'
#                     print tag_p.text
                Indexed['Content'] = content
                Indexed['Labels'] = [ {"Label":"互联网", "Weight":5}]
                mdata['Indexed'] = Indexed
                self.data.append(mdata)        
                return mdata
            except Exception, e:
                print e            
        else:
            self.log('Other Page: ' + response.url)
            return None
    
    
    
    
    def process_raw_links(self, response):
        """ process the link of the response page. including the content links and the page links. get the links and then insert the 
        links into HBase 
        @param response: the Response object of SCRAPY
        @return: the links which have been pre-processed and have been gone through the user patterns """

        links = self.pre_process_links(response)

        return self.user_process_links(response, links)
        
    
    
    
    def post_process_links(self, links):
        """ to process the links yield from the process steps. insert these links into the HBase. If there is some exceptions
        were raised, we just ignore the links we yield and stop inserting into HBase """
        pass
                    
            
    
    
    def pre_process_links(self, response):
        """ process the links. transfer the relative URL to absolute URL. 
        And process the encode problems
        @param response: the Response object of SCRAPY
        @return: the list of new links """
        new_links = set()
        links = response.xpath('//a/@href').extract()
        for l in links:
            l = l.encode('utf8')
            l = urlparse.urljoin(self.response_url, l)
            # to determine whether we need to decode the URLCode for the links
            l = self.process_links_decode(l)
            # origin_url = urllib.unquote(r.request.url)
            new_links.add(l)
        return new_links
    
    
    def process_links_decode(self, link):
        """ process the URLCode stuff for the links. If the user want to decode the URL ( set it in Const.py ), we will
        process the URL for user, or we will return the URL the user passed over  """       
        return link
    
    
    def user_process_links(self, response, links):
        """ Based on the user patterns to process the links. return the links which match user's requirement
        @param links: the links that encoded with UTF-8, and all the links are absolute links. Maybe there are some 
                javascript link just like: javascript:go(10).
        @return: the links that matches the user's requirement. and need to update into HBase, but have not been rows from HBase """
        self.log('begin to user_process_links')
        new_links = set()
        for link in links:
            result = re.search(r'www.36kr.com/p/(\d*).htm', link, re.I)
            if result:
                if link.__contains__('#'):
                    link = link[0:link.index('#')]
                if link.__contains__('?'):
                    link = link[0:link.index('?')]
                new_links.add(link)
        return new_links

    
    def parse(self, response):    
        try:
            self.response_url = self.process_links_decode(response.url)
            self.response_request_url = self.process_links_decode(response.request.url)
            mdata = self.process_raw_content(response)
            if mdata:
                try:
                    mitem = dict()
                    mitem['ItemId'] = mdata['ItemId'].decode('utf-8')
                    mitem['Title'] = mdata['Indexed']['Title']
                    mitem['Url'] = mdata['Url'].decode('utf-8')
                    mitem['Category'] = mdata['Properties']['Category'][2]
                    mitem['Content'] = mdata['Indexed']['Content']
                    mitem['IconUrl'] = mdata['Auxiliary']
                    self.items.append(mitem)
                except Exception, e:
                    print e
        except Exception, e:
            self.log(str(e))                
        
        insert_links = self.process_raw_links(response)        
        
        for link in insert_links:
            mMeta = dict()
            mMeta['category'] = response.meta['category']
            yield scrapy.Request(link, dont_filter=False, meta=mMeta)
    
    
    

    def log(self, msg):
        log.msg(msg, _level=log.INFO)
    
    


    @classmethod
    def from_crawler(cls, crawler, **spider_kwargs):
        """to regist to receive system signal in this method
        @param crawler: crawler object
        @param **spider_kwargs: the parameters needed for scrapyd """
        spider = cls()
        crawler.signals.connect(spider.my_spider_open, signals.spider_opened)
        crawler.signals.connect(spider.my_spider_close, signals.stats_spider_closing)
        crawler.signals.connect(spider.my_spider_idle, signals.spider_idle)
        return spider
    
    
    def set_crawler(self, crawler):
        super(OnceSpider, self).set_crawler(crawler)
    
    
    
    def my_spider_open(self):
        self.log("SPIDER OPEN!!!!!")
        self.spider_time = time.time();
        
        
     
    def my_spider_close(self):
        self.log('SPIDER CLOSE!!!!')
#         self.single_commit()
        self.batch_commit()
        self.output_items()
        
            

    def my_spider_idle(self):
        self.log('SPIDER IDLE!!!!')
        self.single_commit()
    
    
    def output_items(self):
        with codecs.open(str(int(time.time())) + '.json', 'w+b', encoding='utf-8') as myfile:
            jsonstr = json.dumps(self.items, ensure_ascii=False, encoding='utf8')
            myfile.write(jsonstr)
    
    
    def batch_commit(self):
        if len(self.data) > 0:
            postdata = json.dumps(self.data, ensure_ascii=False, encoding='utf8')
            with open('output.out', 'w') as my_out:
                my_out.write(postdata.encode('utf8'))
            res = urllib2.urlopen('http://ds.red.baidu.com/s/100395/200559?token=10da5052dc878be187aec7e043669719', postdata.encode('utf8')).read()
            print res
            self.data = []
    
    def single_commit(self):
        for s_data in self.data:
            postdata = json.dumps(s_data, ensure_ascii=False, encoding='utf8')
            print postdata
            res = urllib2.urlopen('http://ds.red.baidu.com/s/100395/200559?token=10da5052dc878be187aec7e043669719', postdata.encode('utf8')).read()
            print res
        self.data = []
            
    


if __name__ == '__main__':
    my_re = re.compile('data.auto.qq.com/car_brand/index.shtml', flags=0)
    str_link = str('http://data.auto.qq.com/car_brand/index.shtml')
    if not my_re.search(str_link) == None:
        print True
    else:
        print False
