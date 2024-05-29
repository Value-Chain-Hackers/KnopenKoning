import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

class IkeaSpider(scrapy.Spider):
    name = "ikea"
    allowed_domains = ["www.ikea.com","ikea.com"]
    start_urls = ["http://www.ikea.com"]

    rules = (Rule(LinkExtractor(), callback="parse_item", follow=True),)
    
    def parse_item(self, response):
        item = {}
        # store the url of the page
        item["url"] = response.url
        try:
            item["title"] = response.xpath('//title/text()').get()
            # get meta data
            item["meta"] = {}
            for meta in response.xpath('//meta'):
                name = meta.xpath('@name').get()
                content = meta.xpath('@content').get()
                if name is not None and content is not None:
                    item["meta"][name] = content
        except:
            return None
        return item