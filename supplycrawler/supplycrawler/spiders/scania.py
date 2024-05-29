import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class UnileverSpider(CrawlSpider):
    name = "scania"
    allowed_domains = ["scania.com"]
    start_urls = ["https://scania.com"]

    rules = (Rule(LinkExtractor(), callback="parse_item", follow=True),)

    def parse_item(self, response):
        item = {}
        item["title"] = response.xpath('//title').get()
        #item["name"] = response.xpath('//div[@id="name"]').get()
        #item["description"] = response.xpath('//div[@id="description"]').get()
        return item
