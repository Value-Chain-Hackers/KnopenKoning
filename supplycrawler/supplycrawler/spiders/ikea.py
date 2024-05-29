import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

class IkeaSpider(scrapy.Spider):
    name = "ikea"
    allowed_domains = ["www.ikea.com","ikea.com"]
    start_urls = ["http://www.ikea.com"]

    rules = (Rule(LinkExtractor(), callback="parse_item", follow=True),)
    
    def parse_item(self, response):
        for item in response.css('div.item'):
            yield {
                'title': item.css('a::text').get(),
                'link': item.css('a::attr(href)').get(),
            }
