# -*- coding: utf-8 -*-

# Scrapy settings for umedia_service project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'umedia_service'

DOWNLOAD_DELAY = 0.25

DEPTH_LIMIT = 5

SCHEDULER_ORDER = 'BFO'

SPIDER_MODULES = ['umedia_service.spiders']
NEWSPIDER_MODULE = 'umedia_service.spiders'

DOWNLOADER_MIDDLEWARES = {
    'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware' : None,
    'umedia_service.downloadermiddleware.RotateUserAgentMiddleware': 400
}

# ITEM_PIPELINES = {
#     'umedia_service.pipelines.UmediaServicePipeline': 300
# }

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'umedia_service (+http://www.yourdomain.com)'
